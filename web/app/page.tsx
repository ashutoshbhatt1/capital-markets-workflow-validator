"use client";

import { useMemo, useState } from "react";
import { IncidentBrief, scenarios } from "../lib/guardian";

type AnalysisMode = "fixture" | "live";

export default function Home() {
  const [selectedId, setSelectedId] = useState(scenarios[0].id);
  const [brief, setBrief] = useState<IncidentBrief>(scenarios[0].brief);
  const [mode, setMode] = useState<AnalysisMode>("fixture");
  const [running, setRunning] = useState(false);
  const [runCount, setRunCount] = useState(1);
  const scenario = useMemo(
    () => scenarios.find((item) => item.id === selectedId) ?? scenarios[0],
    [selectedId],
  );

  function selectScenario(id: string) {
    const next = scenarios.find((item) => item.id === id) ?? scenarios[0];
    setSelectedId(next.id);
    setBrief(next.brief);
    setMode("fixture");
  }

  async function runExplanation() {
    setRunning(true);
    try {
      const response = await fetch("/api/explain", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ scenarioId: scenario.id }),
      });
      if (!response.ok) throw new Error("Replay mode");
      const payload = (await response.json()) as { brief: IncidentBrief };
      setBrief(payload.brief);
      setMode("live");
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 620));
      setBrief(scenario.brief);
      setMode("fixture");
    } finally {
      setRunning(false);
      setRunCount((count) => count + 1);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="FuturesPlaybook Guardian home">
          <span className="brand-mark" aria-hidden="true">FG</span>
          <span>
            <strong>FuturesPlaybook</strong>
            <small>Guardian</small>
          </span>
        </a>
        <div className="topbar-status" aria-label="System status">
          <span className="status-pill safe"><i /> Execution disabled</span>
          <span className="status-pill model">GPT-5.6 Sol</span>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="kicker">AI-assisted workflow assurance</p>
          <h1>Every decision explained.<br /><span>No guardrail crossed.</span></h1>
          <p className="hero-summary">
            Guardian pairs deterministic controls with a read-only GPT-5.6 Sol incident brief—
            so reviewers get evidence, uncertainty, and the next test without giving AI execution authority.
          </p>
        </div>
        <div className="hero-metrics" aria-label="Validation metrics">
          <article><strong>13</strong><span>tests passing</span></article>
          <article><strong>0</strong><span>AI write paths</span></article>
          <article><strong>3</strong><span>sanitized replays</span></article>
        </div>
      </section>

      <section className="control-room" aria-label="Guardian incident control room">
        <aside className="scenario-rail">
          <div className="section-heading">
            <p>Replay library</p>
            <span>{String(scenarios.length).padStart(2, "0")}</span>
          </div>
          <div className="scenario-list">
            {scenarios.map((item) => (
              <button
                className={`scenario-button ${item.id === scenario.id ? "active" : ""}`}
                key={item.id}
                onClick={() => selectScenario(item.id)}
                aria-pressed={item.id === scenario.id}
              >
                <span>{item.eyebrow}</span>
                <strong>{item.name}</strong>
                <small>{item.context}</small>
                <i className={item.decision === "REJECT" ? "reject-dot" : "review-dot"} />
              </button>
            ))}
          </div>
          <div className="safety-card">
            <span className="lock-icon" aria-hidden="true">×</span>
            <div>
              <strong>Authority boundary</strong>
              <p>AI can explain and recommend tests. It cannot approve, submit, size, or route an action.</p>
            </div>
          </div>
        </aside>

        <div className="workspace">
          <div className="workspace-header">
            <div>
              <p>{scenario.eyebrow} / SANITIZED REPLAY</p>
              <h2>{scenario.name}</h2>
            </div>
            <button className="run-button" onClick={runExplanation} disabled={running}>
              <span aria-hidden="true">{running ? "···" : "▶"}</span>
              {running ? "Analyzing evidence" : "Run Guardian analysis"}
            </button>
          </div>

          <div className="timeline-card">
            <div className="timeline-topline">
              <span>Deterministic decision path</span>
              <code>{scenario.time}</code>
            </div>
            <div className="timeline">
              <article>
                <span className="step-index">01</span>
                <p>Normalized event</p>
                <strong>{scenario.eventId}</strong>
                <small>quality_score = {scenario.value.toFixed(1)}</small>
              </article>
              <div className="connector" aria-hidden="true"><i /></div>
              <article>
                <span className="step-index">02</span>
                <p>Control evaluation</p>
                <strong>Threshold {scenario.threshold.toFixed(1)}</strong>
                <small>Hard maximum {scenario.maximum.toFixed(1)}</small>
              </article>
              <div className="connector" aria-hidden="true"><i /></div>
              <article className={scenario.decision === "REJECT" ? "decision-reject" : "decision-review"}>
                <span className="step-index">03</span>
                <p>System decision</p>
                <strong>{scenario.decision}</strong>
                <small>{scenario.decisionReason}</small>
              </article>
            </div>
          </div>

          <div className="analysis-grid">
            <article className={`brief-card severity-${brief.severity}`}>
              <div className="card-label">
                <span>Guardian incident brief</span>
                <span className={`mode-badge ${mode}`}>
                  {mode === "live" ? "Live GPT-5.6 Sol" : "Verified replay fixture"}
                </span>
              </div>
              <h3>{brief.headline}</h3>
              <p className="brief-summary">{brief.summary}</p>

              <div className="evidence-list">
                {brief.evidence.map((item) => (
                  <div className="evidence-item" key={item.evidence_id}>
                    <code>{item.evidence_id}</code>
                    <div><strong>{item.label}</strong><p>{item.detail}</p></div>
                  </div>
                ))}
              </div>

              <div className="human-action">
                <span>Human action</span>
                <p>{brief.human_action}</p>
              </div>
            </article>

            <aside className="recommendation-card">
              <div className="card-label"><span>Next regression test</span><span>01</span></div>
              {brief.recommended_tests[0] ? (
                <>
                  <code className="test-name">{brief.recommended_tests[0].name}</code>
                  <p>{brief.recommended_tests[0].purpose}</p>
                  <div className="expected-result">
                    <span>Expected</span>
                    <p>{brief.recommended_tests[0].expected_outcome}</p>
                  </div>
                </>
              ) : <p>No additional test was proposed.</p>}
              <div className="uncertainty">
                <span>Known uncertainty</span>
                <p>{brief.uncertainties[0]}</p>
              </div>
              <div className="authorization-proof">
                <span>Execution authorized</span>
                <strong>FALSE</strong>
              </div>
            </aside>
          </div>
        </div>
      </section>

      <footer>
        <p>Built with Codex + GPT-5.6 Sol for OpenAI Build Week.</p>
        <span>Replay run {String(runCount).padStart(3, "0")} · No financial actions · Educational demo</span>
      </footer>
    </main>
  );
}
