# Healia frontend design docs

Markdown-only design workflow (no Figma). Fill these files **before** asking Cursor to rebuild UI.

## Files

| File | Purpose |
|------|---------|
| [../DESIGN.md](../DESIGN.md) | Source of truth: tokens + philosophy + component rules |
| [user-journeys.md](./user-journeys.md) | Who uses Healia, primary flows, page list |
| [wireframes.md](./wireframes.md) | Low-fi layout notes per screen (ASCII or bullet structure) |
| [references.md](./references.md) | URLs/screenshots you like + what to borrow from each |
| [component-inventory.md](./component-inventory.md) | Components you actually need (keeps scope small) |
| [anti-patterns.md](./anti-patterns.md) | Explicit “never do this” list for agents |
| [pipeline-ui.md](./pipeline-ui.md) | How to show backend pipeline events in the UI |

## Suggested order

1. `user-journeys.md` — decide paths and pages to keep/drop  
2. `references.md` — pick 2–3 visual directions  
3. `DESIGN.md` — lock colors, type, spacing  
4. `wireframes.md` — structure each screen  
5. `component-inventory.md` + `anti-patterns.md`  
6. `pipeline-ui.md` — consult/voice experience  
7. Then ask Cursor: *“Rebuild [page] following frontend/DESIGN.md and frontend/docs/*”*

## Agent prompt template

```
Read frontend/DESIGN.md and frontend/docs/ before writing any UI code.
Follow tokens strictly. Do not use forbidden patterns in docs/anti-patterns.md.
Build: [screen name] per docs/wireframes.md section [X].
```
