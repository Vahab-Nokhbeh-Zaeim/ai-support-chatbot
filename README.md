# AI Support Chatbot

A customer-support chatbot API built with **FastAPI**. It answers questions from a FAQ knowledge base using **retrieval-augmented generation (RAG)**: the most relevant FAQ entries are retrieved with TF-IDF and passed to an LLM as context, so answers stay grounded in your own content.

![tests](https://github.com/Vahab-Nokhbeh-Zaeim/ai-support-chatbot/actions/workflows/tests.yml/badge.svg)

## Features

- **RAG pipeline**: TF-IDF retrieval over a JSON knowledge base, implemented from scratch
- **Persian and English**: a bilingual FAQ, Persian text normalization (Arabic ي/ك, half-spaces, Persian digits, plural endings) and replies in the customer's language
- Works with **any OpenAI-compatible API** (OpenAI, local models, other providers)
- **Offline mode**: without an API key the bot answers with the best matching FAQ entry
- Short per-session conversation memory
- Returns the source questions used for every answer
- **Unanswered-questions log**: questions the FAQ cannot answer are saved to a file and ranked, so you know which entries to add next
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

Open http://127.0.0.1:8000 for the bilingual chat page, or http://127.0.0.1:8000/docs for the interactive API docs. The chat page uses the same `/chat`, `/health` and session-reset endpoints as the API.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Enables LLM mode. Without it the bot runs in offline mode |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible endpoint |
| `FAQ_PATH` | `data/faq.json` | Path to the knowledge base |
| `UNANSWERED_LOG` | `data/unanswered.jsonl` | Where unanswered questions are saved. Set it to an empty value to turn the log off |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service status and mode (`llm` or `offline`) |
| `POST` | `/chat` | Ask a question |
| `GET` | `/unanswered?limit=20` | Most common questions the FAQ could not answer |
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

### Persian example

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "میخوام کالا رو مرجوع کنم"}'
```

```json
{
  "answer": "بله. هر کالای استفاده‌نشده را تا ۷ روز پس از تحویل می‌توانید مرجوع کنید...",
  "sources": ["آیا امکان مرجوع کردن کالا وجود دارد؟"],
  "mode": "offline"
}
```

The retriever normalizes Persian text before matching, so `پيگيري` (Arabic keyboard), `پیگیری`, `سفارش‌ها` and `سفارشها` all find the same entries.

## Improving the FAQ with unanswered questions

When the retriever finds no matching FAQ entry, the original message is appended to `data/unanswered.jsonl` (one JSON object per line, Persian text stored as readable UTF-8). This happens in both offline and LLM mode; an LLM answer that is uncertain is not logged when the retriever found a match:

```json
{"time": "2026-11-21T09:30:12+00:00", "language": "fa", "message": "کارت هدیه دارید؟"}
```

`GET /unanswered` groups questions that differ only in spelling, punctuation or keyboard (`كارت هديه` and `کارت هدیه دارید؟` count as one) and lists the most frequent first:

```json
{
  "total": 3,
  "questions": [
    {"question": "كارت هديه داريد", "count": 2, "language": "fa", "last_asked": "2026-11-21T09:41:03+00:00"},
    {"question": "Is there a store in Tabriz?", "count": 1, "language": "en", "last_asked": "2026-11-21T09:35:47+00:00"}
  ]
}
```

Each entry stores the original message text, its detected language and a UTC timestamp. Session IDs are not stored, but message text is kept as submitted and may contain personal information. Do not include passwords, payment details or other sensitive information in chat messages. Set `UNANSWERED_LOG` to an empty value to disable the log. The log file is git-ignored, and `DELETE /chat/{session_id}` clears only in-memory conversation history; it does not erase logged questions.

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
