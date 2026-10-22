# AI Agent Manager — Streamlit Starter

Starter project for a central chat + multi-agent planning dashboard. It can generate a structured plan using the OpenAI API, or run in demo mode without an API key.

## What it does
- Central chat for entering a goal.
- AI-generated task plans with agent roles, dependencies, risks and success criteria.
- Dashboard for current-session jobs and task counts.
- Agent registry page.
- Human-approval flags for high-risk/external actions.
- Demo fallback if no API key is configured.

## What it does NOT do yet
- It does not execute external actions, browse the web, publish YouTube videos, send emails, or run arbitrary code.
- It does not provide persistent job storage. Streamlit session state is temporary.
- It is not a production-grade authorization or audit system.
- It does not guarantee 24/7 execution.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository, for example `ai-agent-manager`.
2. Upload `app.py`, `requirements.txt`, and `README.md`.
3. Open https://share.streamlit.io/ and sign in with GitHub.
4. Create an app and select the repository, branch, and `app.py`.
5. Deploy. The app works in demo mode without a key.
6. To enable AI planning, open the app's settings/secrets area and add:

```toml
OPENAI_API_KEY = "your-api-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

Never commit API keys to GitHub. API usage may cost money and is billed separately from Streamlit hosting.

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Recommended production architecture
Keep Streamlit as the UI. Put the actual workers and scheduler in a separate backend (for example a Python service using a task queue), use a persistent database such as PostgreSQL, and protect external actions with server-side authorization and audit logs. Do not rely on the Streamlit app process for 24/7 background work.

## Before connecting real tools
- Add authentication and user authorization.
- Store API credentials in the host's secret manager.
- Add a persistent database and audit trail.
- Add idempotency keys and bounded retries.
- Enforce human approval server-side before publishing, sending, purchasing, deleting or changing external data.
- Test with sandbox accounts and private/draft outputs first.
