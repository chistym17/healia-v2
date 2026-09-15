# Healia database

PostgreSQL via Supabase. Auth is **email + password** via Supabase Auth (no Google).

## Tables

| Table | Purpose |
|---|---|
| `users` | Profiles (`id` matches Supabase Auth user id) |
| `session_history` | Consultations |
| `session_results` | Guidance (1:1 with session) |

## Apply schema

Run [`schema.sql`](./schema.sql) in Supabase SQL Editor.

## Env

See [`.env.example`](./.env.example). Put values in `backend/.env`.

For local testing, disable email confirmation:
**Authentication → Providers → Email → Confirm email → off**.
