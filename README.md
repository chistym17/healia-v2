# Healia

Calm, voice-first AI health consultation. Users describe symptoms, answer focused follow-ups, and get evidence-based guidance — not a diagnosis.

## Architecture

```text
React (Vite)  →  FastAPI  →  LiveKit agent
                    ↓              ↓
               Supabase Auth   Assessment RAG (MedQuAD)
               Session history Knowledge RAG (StatPearls / hybrid FAISS+BM25)
                    ↓              ↓
               Postgres        Embeddings (local TEI or Hugging Face MiniLM)
```

**Product docs (source of truth):**

- [`frontend/PRODUCT.md`](frontend/PRODUCT.md) — scope & journey
- [`frontend/UX.md`](frontend/UX.md) — interaction rules
- [`frontend/DESIGN.md`](frontend/DESIGN.md) — visual system
- [`db/README.md`](db/README.md) — schema & Supabase setup

## Stack

| Layer | Tech |
|---|---|
| Frontend | React, Vite, Tailwind |
| API | FastAPI (auth, sessions, LiveKit token) |
| Voice | LiveKit + AssemblyAI STT + Google TTS |
| Data | Supabase Auth + Postgres (RLS) |
| RAG | FAISS + BM25, optional BGE rerank |
| Bot check | Cloudflare Turnstile (signup) |

## Local run (short)

1. Apply [`db/schema.sql`](db/schema.sql) in Supabase; copy [`db/.env.example`](db/.env.example) → `backend/.env`.
2. Frontend: copy [`frontend/.env.example`](frontend/.env.example) → `frontend/.env`.
3. Backend: `cd backend && uvicorn main:app --reload --port 8000`
4. Agent: run the LiveKit worker from `backend/livekit_agent` (see that package).
5. Frontend: `cd frontend && npm install && npm run dev` (port 3000).

Embeddings:

- Local: `EMBEDDING_PROVIDER=local` + TEI at `EMBEDDING_SERVER`
- Deploy / no TEI: `EMBEDDING_PROVIDER=huggingface` + `HF_TOKEN` (same MiniLM model as the indexes)

Keep `RERANK_ENABLED=false` unless a rerank server is running.

## Disclaimer

Healia provides educational guidance only. It is not a medical diagnosis or substitute for professional care. For emergencies, seek urgent care.
