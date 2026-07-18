# Guardian control room

The full-stack dashboard for FuturesPlaybook Guardian. It is built with vinext and deploys through OpenAI Sites.

```bash
npm install
npm run dev
```

The UI is useful without an API key: when live AI is disabled, it loads a verified replay fixture and labels it clearly. To test GPT-5.6 Sol locally, copy `.env.example` to `.env.local`, provide `OPENAI_API_KEY`, and set `ENABLE_LIVE_AI=true`.

The worker only accepts the three known scenario IDs. It never accepts an arbitrary prompt, validates every evidence reference against the supplied bundle, and rejects any response that does not keep `execution_authorized` false.

Useful checks:

```bash
npm run lint
npm test
```
