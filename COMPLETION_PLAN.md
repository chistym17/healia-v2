# Healia — Project Completion Plan

**Purpose:** Connect the finished consultation pipeline to the v2 product UI and make Healia a fully finished product — including users and saved consultations.

**Last updated:** 2026-09-04

**Current reality (short):**

- Backend voice consultation pipeline is largely built (LiveKit agent + supervisor + assessment RAG + knowledge RAG + spoken guidance + pipeline events).
- Frontend v2 product UI is largely built (landing + prep → session → processing → results) but runs on **mocks**.
- The only real LiveKit frontend path is the developer test page `/live-voice`.
- There is **no database**, **no user accounts**, and **no saved consultations** today (state is in-memory; logs are files only).
- The gap is not “build the brain” — it is **connect, persist, harden, and ship**.

---

## 1. Current Status Snapshot

### What is already done

| Area | Status |
|---|---|
| Medical RAG indexes (StatPearls + MedQuAD assessment) | Done |
| LiveKit agent worker (`healia`) | Done |
| Supervisor-controlled consultation turns | Done |
| Knowledge retrieval + grounded guidance generation | Done |
| Speak guidance over voice | Done |
| Pipeline events on LiveKit topic `healia.pipeline` | Done |
| FastAPI LiveKit token endpoint | Done |
| v2 homepage (design system) | Done |
| v2 consultation UI flow (prep / session / processing / results) | Done (mocked) |
| Product / UX / Design specs | Done |

### What is partial

| Area | Gap |
|---|---|
| LiveKit ↔ product UI | Real only on `/live-voice`, not `/v2/consultation/session` |
| Guidance shape | Backend returns `spoken_answer` / `detailed_answer` / `citations` / `confidence` — Results UI expects Summary / Actions / Warnings / Seek care / References |
| Processing screen | Timer-based mock; not driven by real pipeline events |
| Session completion | Agent speaks guidance and stays in room; no clean handoff to Processing → Results |
| Text fallback | Mock only; not sent into LiveKit / supervisor |
| Ops / docs | No solid `.env.example`, runbook, or backend README for running API + agent + embed/rerank |

### What is missing for a finished product

1. Wire v2 session to LiveKit (replace mocks).
2. Subscribe to pipeline events for transcript progress + processing steps.
3. Reshape / extend guidance into Results UX structure.
4. Deliver full guidance payload to frontend (data channel + HTTP).
5. End-of-consultation → Processing → Results navigation that uses real data.
6. **Database for users and consultations** (none today).
7. **Auth (sign up / sign in) and ownership of consultations.**
8. **Save transcript + structured guidance; allow users to reopen past results.**
9. Error handling users can recover from (mic, connect, processing fail).
10. Runbook + env setup so anyone can start the full stack.
11. End-to-end testing and polish (About / Privacy content, disclaimers, mobile).
12. Decide what to do with legacy paths (`/conversation`, `/consultation`, old diagnose APIs).

---

## 2. Target End-to-End User Flow

```text
Landing (/v2)
   ↓
Sign up / Sign in  (or continue as guest → prompt to save after results)
   ↓
Prep (/v2/consultation)
   ↓
Live session (/v2/consultation/session)  ← LiveKit + agent
   ↓  (assessment complete / guidance ready)
Processing (/v2/consultation/processing) ← driven by pipeline events
   ↓
Results (/v2/consultation/results)       ← structured guidance + references
   ↓
Saved to DB under the user
   ↓
Consultation history (list + reopen past results)
```

**Runtime pieces that must be up for a real consultation:**

1. FastAPI backend (token API + auth + consultation/results APIs)
2. Database (users + consultations + guidance)
3. LiveKit agent worker (`python -m livekit_agent.agent`)
4. LiveKit cloud/project credentials
5. Embedding server (assessment + knowledge RAG)
6. Optional rerank server (when mode = `rerank`)
7. Frontend Vite app (`/v2`)

---

## 3. Architecture Decision (recommended)

Keep **LiveKit as the consultation transport**. Do not rebuild consultation on the legacy `/api/audio` path.

```text
Frontend v2 Session
   → Auth (JWT / session cookie)
   → POST /api/livekit/token
   → LiveKit room + agent "healia"
   → Voice in / voice out
   → Subscribe to topic: healia.pipeline
   → On guidance ready:
        agent/API persists consultation + guidance to DB
        frontend navigates Processing → Results
   → GET /api/consultations/{id}  (reload-safe Results)
   → GET /api/consultations       (history for signed-in user)
```

**Persistence is required for the finished product** (not optional):

- LiveKit data channel = live progress
- Database + HTTP = durable Results, history, and refresh-safe pages

### Recommended data model (v1)

Keep it simple — not a complex medical dashboard.

```text
users
  id
  email
  password_hash (or auth-provider id)
  name (optional)
  created_at

consultations
  id
  user_id (nullable if guest → claim later)
  livekit_room_name / session_id
  status: started | in_progress | processing | completed | failed
  started_at
  completed_at

consultation_turns  (optional but useful)
  id
  consultation_id
  role: user | healia
  text
  created_at

consultation_results
  id
  consultation_id (unique)
  summary
  possible_concerns
  actions (JSON)
  warning_signs
  seek_care
  references (JSON)
  spoken_answer (optional)
  confidence (optional)
  raw_guidance (JSON, optional for debug)
  created_at
```

**Product UX constraint:** history should be a calm list of past consultations + reopen Results — not a heavy account/dashboard product.

---

## 4. Schema Gap to Resolve Early

### Backend guidance today

```text
spoken_answer
detailed_answer
citations[]
confidence
```

### Frontend Results UX needs

```text
summary
possibleConcerns
actions[]
warningSigns
seekCare
references[]
```

**Decision required in Phase 1:**

- **Option A (recommended):** Extend `guidance_agent` JSON to emit Results sections directly (plus `spoken_answer` for voice).
- **Option B:** Keep current guidance and map/summarize into Results fields on the frontend or a thin backend adapter.

Prefer Option A so Results quality is owned by the backend prompt, not fragile frontend string-splitting.

Also lock the **DB entities** (users / consultations / results) in Phase 1 so Phase 4 does not invent a second schema.

---

## 5. Phased Work Plan

### Phase 0 — Foundation & Runbook (1–2 days)

**Goal:** Anyone on the team can run the full stack and verify the real voice path.

**Work**

- Document required env vars (API keys, LiveKit, embed/rerank URLs, **database URL**).
- Add `.env.example` for backend (and frontend `VITE_API_URL`).
- Write a short runbook: start FastAPI, agent worker, embed server, frontend, **database**.
- Confirm `/live-voice` works end-to-end on a clean machine.
- Inventory indexes: MedQuAD assessment + StatPearls knowledge present and loadable.
- Align naming: one frontend env (`VITE_API_URL`), deprecate confusion with `VITE_SERVER_URL`.

**Exit criteria**

- [ ] Fresh checkout + env → `/live-voice` completes a short consultation with spoken guidance.
- [ ] Pipeline events visible in agent logs and (optionally) room data channel.

---

### Phase 1 — Contract & Handoff Design (1–2 days)

**Goal:** Define the product contracts before coding glue — including persistence.

**Work**

- Finalize guidance JSON schema for Results UX (Option A preferred).
- Define pipeline event types the frontend will use, especially:
  - turn started / completed
  - assessment progress (user-facing labels only)
  - case package ready
  - knowledge retrieval started / completed
  - guidance completed (**include full payload or consultation/results id**)
  - consultation ended / escalated / error
- Decide Results delivery:
  - Live progress via `healia.pipeline`
  - **Durable Results via DB + HTTP** (`GET /api/consultations/{id}`)
- Define user/auth approach for finished product:
  - email + password **or** magic link / OAuth (pick one simple path)
  - guest consultation allowed? (recommended: yes, then “Save to account” on Results)
- Define session lifecycle: when does UI leave Session → Processing?
  - Recommended trigger: `guidance.completed` or supervisor `build_final_query` + guidance ready
- Map LiveKit voice assistant states → v2 `VoiceState`.
- Decide text-fallback transport (LiveKit chat/data message into agent).
- Lock v1 data model (users, consultations, results, optional turns).

**Exit criteria**

- [ ] Written API/event/data contract checked into repo (`docs/CONTRACT.md` or this plan).
- [ ] Frontend `GuidanceResult` type and backend guidance schema agree.
- [ ] Auth + persistence approach decided (guest policy included).

---

### Phase 2 — Wire Live Session (core integration) (3–5 days)

**Goal:** `/v2/consultation/session` uses real LiveKit instead of mock turns.

**Work**

- Create shared frontend LiveKit/API client (token fetch, room helpers).
- Replace `useConsultationSession` mocks with LiveKit session start/end.
- Reuse patterns from `LiveVoicePage` (token source, agent name `healia`, audio defaults).
- Map agent state → `VoiceStateIndicator`.
- Build transcript from real user/agent utterances (STT / agent messages / pipeline events — pick one reliable source).
- Keep v2 calm UI (no LiveKit default ControlBar chrome unless restyled).
- Wire mic permission and connection errors to friendly UX copy.
- Keep “End consultation” as an explicit user action; also auto-advance when guidance is ready (prefer auto-advance after guidance spoken, with End as escape hatch).

**Exit criteria**

- [ ] User can complete a real voice consultation from `/v2/consultation` prep → session.
- [ ] Transcript and voice states update from live session.
- [ ] Mocks no longer required for session path (keep mock flag for offline UI work if useful).

---

### Phase 3 — Processing + Results Handoff (2–4 days)

**Goal:** Processing and Results use real pipeline data (persist path prepared for Phase 4).

**Work**

- Subscribe to `healia.pipeline` in the frontend.
- Drive ProcessingSteps from real events (reviewing symptoms / checking references / preparing results) — no fake percentages, no fake timers as primary source.
- Extend backend guidance output to Results sections (or adapter).
- Deliver full guidance payload to frontend (data channel and/or temporary in-memory/HTTP handoff until DB lands).
- Navigate Session → Processing → Results with real data.
- Show references with source + title (and link when available).
- Keep medical disclaimer + warning visual hierarchy.
- Emit a stable `consultation_id` / `session_id` the frontend can use once DB persistence is live.

**Exit criteria**

- [ ] Ending a consultation lands on Results with real, structured content.
- [ ] Guidance payload shape matches Results UX.
- [ ] Warnings / seek-care sections are never empty when clinically relevant (prompt + validation).

---

### Phase 4 — Users, Auth & Consultation Persistence (required for finished product) (4–6 days)

**Goal:** Users can create accounts and Healia saves consultations so Results and history survive refresh and return visits.

**This phase is in scope for the finished product — not post-v1.**

**Work**

**Database & backend**

- Choose and set up DB (recommended: **PostgreSQL**; SQLite acceptable only for local MVP if needed).
- Add migrations / ORM layer (SQLAlchemy, Prisma-style equivalent, or similar — follow existing Python stack).
- Implement tables: `users`, `consultations`, `consultation_results` (+ optional `consultation_turns`).
- Auth APIs: register, login, logout, current user (`/api/auth/*`).
- Consultation APIs:
  - create/start consultation (link LiveKit room / session id)
  - update status
  - save turns (optional streaming or batch at end)
  - save final structured results when guidance completes
  - `GET /api/consultations` (current user history)
  - `GET /api/consultations/{id}` (results + metadata)
- Agent/API handoff: when guidance completes, **persist results to DB** (agent calls FastAPI internal endpoint, or FastAPI listens and writes).
- Associate consultation with `user_id` when signed in; support guest → claim/save later if guest mode is enabled.

**Frontend**

- Sign up / Sign in pages under `/v2` (calm, minimal — match DESIGN.md).
- Auth state in frontend (token/cookie); protect history routes.
- After Results: show “Saved to your account” (or prompt to create account if guest).
- Consultation history page: simple list (date, short summary, status) → open past Results.
- Results page loads from `GET /api/consultations/{id}` (refresh-safe).
- Privacy copy updated: what is stored (account, transcript/results), retention basics.

**Security / privacy (minimum for finished product)**

- Hash passwords (or use managed auth).
- Authorize: users can only access their own consultations.
- Do not log raw credentials; avoid dumping full medical transcripts to client console.
- Document retention: e.g. consultations kept until user deletes account / requests deletion (even if delete UI is simple).

**Exit criteria**

- [ ] User can sign up, sign in, and sign out.
- [ ] Completing a consultation saves structured Results to the DB.
- [ ] User can reopen a past consultation from history.
- [ ] Refreshing Results still works via consultation id.
- [ ] Users cannot read another user’s consultations.
- [ ] Privacy page accurately describes stored data.

---

### Phase 5 — Product Completeness (2–3 days)

**Goal:** The app feels finished for a real user, not a demo.

**Work**

- About page: what Healia is, limitations, not a doctor.
- Privacy page: data processed (voice, transcript, saved results), account data, retention.
- Text fallback into the live pipeline.
- Empty / error states for: mic denied, token fail, agent not connected, guidance fail, network drop, auth fail.
- “New consultation” resets cleanly (leave room, clear context, create new DB consultation).
- Mobile pass: auth, session controls, transcript, results, history.
- Accessibility: labels, focus, reduced motion on voice visuals.
- Soft-deprecate or hide legacy routes from v2 navigation — keep `/live-voice` as internal/dev if needed.

**Exit criteria**

- [ ] A non-technical user can go homepage → account → consultation → results → history without developer instructions.
- [ ] Failures explain what happened and what to do next.

---

### Phase 6 — Hardening, Testing & Launch Readiness (2–4 days)

**Goal:** Reliable enough to ship and iterate with real users.

**Work**

- Manual E2E script (happy path + failure cases), including auth + saved history.
- Latency checklist (greeting, follow-up TTFB, guidance generation, DB save).
- Supervisor / RAG quality spot-checks on 10–20 common symptom scenarios.
- Logging hygiene: user-facing UI never shows technical errors; backend logs remain detailed.
- Config cleanup: env-driven DB/auth/LiveKit settings; document `livekit_agent/config.py` knobs.
- Security pass: CORS lockdown, secrets only on server, auth on consultation APIs.
- Production deploy notes (frontend, API, agent worker, LiveKit, **database**).
- Backup / migration notes for production DB.

**Exit criteria**

- [ ] Written E2E test checklist passes on staging (including save + reopen consultation).
- [ ] Known issues list documented (acceptable vs blockers).
- [ ] Deploy steps written (including DB).

---

### Phase 7 — Post-v1 (explicitly out of finished v1)

Do **not** block finished v1 on these:

- Complex clinical dashboard / analytics
- Family profiles / multi-patient households
- Appointment booking / payments
- Multi-language
- Full HIPAA compliance program (document current limitations; store carefully)
- Replacing LiveKit with custom WebRTC
- Large marketing site
- Perfect diagnostic accuracy claims
- Social features

> Note: **basic users + saved consultations are in Phase 4 (in scope).** Only heavy account/dashboard expansion stays post-v1.

---

## 6. Suggested Order of Execution

```text
Phase 0  Runbook + prove /live-voice
   ↓
Phase 1  Contracts (guidance schema + events + auth/DB model)
   ↓
Phase 2  Wire v2 Session to LiveKit
   ↓
Phase 3  Processing + Results real data
   ↓
Phase 4  Users + DB + save/reopen consultations   ← required for finished product
   ↓
Phase 5  About/Privacy/errors/mobile polish
   ↓
Phase 6  E2E testing + deploy readiness
```

Phases 2–4 are the critical path for a finished product. Phase 0–1 prevent rework. Phase 5–6 make it shippable.

---

## 7. Workstream Split (parallelizable)

| Stream | Owner focus | Phases |
|---|---|---|
| **A. Backend handoff** | Guidance schema, results payload, session complete signal | 1, 3 |
| **B. Frontend integration** | LiveKit in v2 session, event subscription, navigation | 2, 3 |
| **C. Users & persistence** | DB, auth, consultation APIs, history UI | 1, 4 |
| **D. Product polish** | About/Privacy, errors, mobile, copy | 5 |
| **E. Ops** | Env, runbook, deploy, E2E checklist | 0, 6 |

---

## 8. Definition of “Fully Complete” (finished product)

Healia is complete when:

1. User starts from `/v2` and finishes with real structured Results.
2. Voice consultation uses the LiveKit agent pipeline (not mocks).
3. Processing reflects real progress.
4. Results include summary, next steps, warnings, seek-care, and references.
5. **Users can sign up / sign in.**
6. **Completed consultations (transcript + structured guidance) are saved to a database.**
7. **Users can open consultation history and reopen past Results.**
8. Results survive page refresh via consultation id.
9. Errors are recoverable and non-technical.
10. About + Privacy exist and accurately describe stored data.
11. Full stack (including DB) can be started from documented steps.
12. Legacy demo paths are not required for the main product journey.

---

## 9. Immediate Next Action

Start **Phase 0 + Phase 1** together:

1. Prove `/live-voice` on a clean env.
2. Lock the Results guidance JSON schema.
3. Lock auth + DB approach (PostgreSQL recommended; guest policy; history UX scope).
4. Decide how the agent writes final guidance into the API/DB.

Then begin **Phase 2** (wire session) without waiting for perfect polish. Start Phase 4 scaffolding (DB + auth) in parallel once Phase 1 contracts are locked.

---

## 10. Key Files Reference

### Backend (keep / extend)

- `backend/livekit_agent/agent.py` — worker entry
- `backend/livekit_agent/consultation.py` — turn pipeline
- `backend/livekit_agent/guidance_agent.py` — guidance JSON (extend for Results)
- `backend/livekit_agent/guidance_pipeline.py` — RAG + guidance orchestration
- `backend/livekit_agent/pipeline_events.py` / `room_events.py` — UI events
- `backend/api/livekit.py` — token API
- `backend/main.py` — FastAPI app
- **New (Phase 4):** auth routes, consultation routes, DB models/migrations

### Frontend (replace mocks / wire)

- `frontend/src/v2/pages/consultation/*` — product flow
- `frontend/src/v2/context/ConsultationContext.tsx` — session state
- `frontend/src/v2/hooks/useConsultationSession.ts` — **replace mocks**
- `frontend/src/v2/hooks/useConsultationProcessing.ts` — **replace mocks**
- `frontend/src/v2/types/consultation.ts` — align with backend schema
- `frontend/src/pages/LiveVoicePage.tsx` — reference LiveKit wiring
- **New (Phase 4):** auth pages, consultation history page, API client for consultations

### Specs (source of truth)

- `frontend/PRODUCT.md`
- `frontend/UX.md`
- `frontend/DESIGN.md`
