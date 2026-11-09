# AI Support Chatbot

A customer-support chatbot API built with **FastAPI**. It answers questions from a FAQ knowledge base using **retrieval-augmented generation (RAG)**: the most relevant FAQ entries are retrieved with TF-IDF and passed to an LLM as context, so answers stay grounded in your own content.

![tests](https://github.com/Vahab-Nokhbeh-Zaeim/ai-support-chatbot/actions/workflows/tests.yml/badge.svg)

## Features

- **RAG pipeline**: TF-IDF retrieval over a JSON knowledge base, implemented from scratch
- Works with **any OpenAI-compatible API** (OpenAI, local models, other providers)
- **Offline mode**: without an API key the bot answers with the best matching FAQ entry
- Short per-session conversation memory
- Returns the source questions used for every answer
- Input validation with Pydantic, auto-generated OpenAPI docs
- Docker support and automated tests

## How It Works

```
User message ──► TF-IDF retriever ──► top FAQ entries
                                            │
                                            ▼
              system prompt + context + history ──► LLM ──► answer + sources
```

## Getting Started

```bash
git clone https://github.com/Vahab-Nokhbeh-Zaeim/ai-support-chatbot.git
cd ai-support-chatbot
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API docs.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Enables LLM mode. Without it the bot runs in offline mode |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible endpoint |
| `FAQ_PATH` | `data/faq.json` | Path to the knowledge base |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service status and mode (`llm` or `offline`) |
| `POST` | `/chat` | Ask a question |
| `DELETE` | `/chat/{session_id}` | Clear a session's history |

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Can I return a product?", "session_id": "user-1"}'
```

```json
{
  "answer": "Yes. You can return any unused product within 7 days of delivery...",
  "sources": ["Can I return a product?"],
  "mode": "offline"
}
```

## Docker

```bash
docker build -t ai-support-chatbot .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key ai-support-chatbot
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## License

[MIT](LICENSE) © Vahab Nokhbeh Zaeim
