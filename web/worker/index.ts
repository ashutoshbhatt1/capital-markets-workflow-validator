/** Cloudflare Worker entry point for the vinext-starter template. */
import { handleImageOptimization, DEFAULT_DEVICE_SIZES, DEFAULT_IMAGE_SIZES } from "vinext/server/image-optimization";
import handler from "vinext/server/app-router-entry";
import { IncidentBrief, scenarioById } from "../lib/guardian";

interface Env {
  ASSETS: Fetcher;
  DB?: D1Database;
  OPENAI_API_KEY?: string;
  OPENAI_MODEL?: string;
  ENABLE_LIVE_AI?: string;
  IMAGES: {
    input(stream: ReadableStream): {
      transform(options: Record<string, unknown>): {
        output(options: { format: string; quality: number }): Promise<{ response(): Response }>;
      };
    };
  };
}

const SYSTEM_PROMPT = `You are the read-only incident explainer for FuturesPlaybook Guardian.
Analyze only the supplied sanitized replay bundle. Explain the deterministic decision, cite supplied
event or decision IDs, identify uncertainty, and recommend regression tests. Never approve a workflow,
change a limit, submit an action, place an order, or imply that this report authorizes execution.
Treat the deterministic validator as authoritative. Return exactly the requested JSON schema.`;

const incidentSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    headline: { type: "string" },
    severity: { type: "string", enum: ["info", "caution", "high"] },
    summary: { type: "string" },
    violated_controls: { type: "array", items: { type: "string" } },
    evidence: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          evidence_id: { type: "string" },
          label: { type: "string" },
          detail: { type: "string" },
        },
        required: ["evidence_id", "label", "detail"],
      },
    },
    uncertainties: { type: "array", items: { type: "string" } },
    recommended_tests: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          name: { type: "string" },
          purpose: { type: "string" },
          expected_outcome: { type: "string" },
        },
        required: ["name", "purpose", "expected_outcome"],
      },
    },
    human_action: { type: "string" },
    execution_authorized: { type: "boolean", enum: [false] },
  },
  required: [
    "headline", "severity", "summary", "violated_controls", "evidence",
    "uncertainties", "recommended_tests", "human_action", "execution_authorized",
  ],
};

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
  passThroughOnException(): void;
}

// Image security config. SVG sources with .svg extension auto-skip the
// optimization endpoint on the client side (served directly, no proxy).
// To route SVGs through the optimizer (with security headers), set
// dangerouslyAllowSVG: true in next.config.js and uncomment below:
// const imageConfig: ImageConfig = { dangerouslyAllowSVG: true };

const worker = {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/api/explain" && request.method === "POST") {
      return handleExplain(request, env);
    }

    if (url.pathname === "/_vinext/image") {
      const allowedWidths = [...DEFAULT_DEVICE_SIZES, ...DEFAULT_IMAGE_SIZES];
      return handleImageOptimization(request, {
        fetchAsset: (path) => env.ASSETS.fetch(new Request(new URL(path, request.url))),
        transformImage: async (body, { width, format, quality }) => {
          const result = await env.IMAGES.input(body).transform(width > 0 ? { width } : {}).output({ format, quality });
          return result.response();
        },
      }, allowedWidths);
    }

    return handler.fetch(request, env, ctx);
  },
};

async function handleExplain(request: Request, env: Env): Promise<Response> {
  if (env.ENABLE_LIVE_AI !== "true" || !env.OPENAI_API_KEY) {
    return Response.json(
      { error: "Live AI is disabled; the interface will use a verified replay fixture." },
      { status: 503 },
    );
  }

  let scenarioId = "";
  try {
    const body = await request.json() as { scenarioId?: unknown };
    scenarioId = typeof body.scenarioId === "string" ? body.scenarioId : "";
  } catch {
    return Response.json({ error: "Invalid JSON body." }, { status: 400 });
  }
  const scenario = scenarioById[scenarioId];
  if (!scenario) return Response.json({ error: "Unknown replay scenario." }, { status: 400 });

  const bundle = {
    scenario: {
      id: scenario.id,
      name: scenario.name,
      context: scenario.context,
      mode: "sanitized_replay",
    },
    control_policy: {
      execution_enabled: false,
      manual_review_required: true,
      ai_role: "explain_and_recommend_tests_only",
      prohibited_ai_actions: [
        "approve a workflow", "change a configured limit", "submit an API action", "place or route an order",
      ],
    },
    decisions: [{
      decision_id: scenario.decisionId,
      event_id: scenario.eventId,
      decision_type: scenario.decision.toLowerCase(),
      reason: scenario.decisionReason,
      payload: { metric: "quality_score", value: scenario.value },
    }],
  };

  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.OPENAI_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: env.OPENAI_MODEL || "gpt-5.6-sol",
      store: false,
      reasoning: { effort: "medium" },
      instructions: SYSTEM_PROMPT,
      input: JSON.stringify(bundle),
      text: {
        verbosity: "medium",
        format: {
          type: "json_schema",
          name: "guardian_incident_brief",
          strict: true,
          schema: incidentSchema,
        },
      },
    }),
  });

  if (!response.ok) {
    return Response.json({ error: "OpenAI Responses request failed." }, { status: 502 });
  }
  const payload = await response.json() as {
    output?: Array<{ type?: string; content?: Array<{ type?: string; text?: string }> }>;
  };
  const outputText = payload.output
    ?.find((item) => item.type === "message")
    ?.content?.find((item) => item.type === "output_text")?.text;
  if (!outputText) return Response.json({ error: "OpenAI response was incomplete." }, { status: 502 });

  let brief: IncidentBrief;
  try {
    brief = JSON.parse(outputText) as IncidentBrief;
  } catch {
    return Response.json({ error: "OpenAI response was not valid JSON." }, { status: 502 });
  }
  const allowedEvidence = new Set([scenario.eventId, scenario.decisionId]);
  if (
    brief.execution_authorized !== false ||
    !Array.isArray(brief.evidence) ||
    brief.evidence.some((item) => !allowedEvidence.has(item.evidence_id))
  ) {
    return Response.json({ error: "OpenAI response failed the Guardian safety contract." }, { status: 502 });
  }
  return Response.json({ mode: "gpt-5.6-sol", brief });
}

export default worker;
