# Local JLens Playground — Agent Guide

## Quick start

```bash
./run.sh              # single command: creates env, installs deps, starts both servers
make backend          # backend only (terminal 1)
make frontend         # frontend dev server only (terminal 2)
make test             # pytest (no real models needed)
```

Backend: `http://127.0.0.1:8787` · Frontend: `http://127.0.0.1:5173`

## Architecture

| Path | What |
|------|------|
| `backend/app/main.py` | FastAPI app — route definitions, logging, comparison logic |
| `backend/app/config.py` | Config loading: `models.example.json` (tracked) + `models.local.json` (gitignored) |
| `backend/app/runner.py` | Model/lens loading, `Loaded` class, analysis + generation with timing |
| `backend/app/demo.py` | Synthetic demo analysis + chat generation + intervened generation |
| `backend/app/schemas.py` | All Pydantic models (request/response types) |
| `backend/app/chat_templates.py` | Chat prompt formatting (native template or fallback) |
| `backend/app/generation.py` | Clean text generation helper |
| `backend/app/interventions/__init__.py` | Intervention package |
| `backend/app/interventions/schemas.py` | Intervention config model |
| `backend/app/interventions/vector_lookup.py` | Lens vector extraction |
| `backend/app/interventions/hooks.py` | Forward-hook intervention engine |
| `frontend/src/actions.js` | App orchestrator — `renderAll()`, `analyze()`, `boot()`, `setActiveTab()` |
| `frontend/src/state.js` | Central state singleton (includes chat + intervention state) |
| `frontend/src/api.js` | API client (includes chat + intervention endpoints) |
| `frontend/src/render/*.js` | One module per UI component |
| `frontend/src/utils/*.js` | escape, colors, ranks, filters |
| `configs/models.example.json` | Tracked model configs (demo + examples) |
| `configs/models.local.json` | Untracked local configs (never commit) |
| `tests/test_demo.py` | Demo analysis tests |
| `tests/test_api.py` | API endpoint tests with `TestClient` |
| `tests/test_config.py` | Config loading + local override tests |
| `tests/test_aggregation.py` | Purely data-driven aggregation tests |
| `tests/test_chat_templates.py` | Chat template formatting tests |
| `tests/test_intervention_schemas.py` | Intervention config schema tests |
| `tests/test_generation_demo.py` | Demo chat generation tests |
| `tests/test_compare_response_shape.py` | Clean vs intervened response shape tests |

## Key conventions

- **No React.** Vanilla JS + Vite only. All modules under `frontend/src/`.
- **No Docker.** Use `run.sh` or `make backend` + `make frontend` in two terminals.
- **CSS** is in `frontend/src/styles/app.css` — readable sections, no minification.
- **Local configs** go in `configs/models.local.json` — gitignored. Never edit `models.example.json` for local configs.
- **Lens `.pt` files** go under `lenses/` — gitignored. Setup via `scripts/setup_config.py`.
- **Model downloads** happen at runtime via Hugging Face; no weights are committed.
- **Tabs** in UI: Prompt Analysis, Chat, Compare, Diagnostics. Chat has generation controls, intervention panel, and trace table.
- **Interventions** are experimental. Additive steering uses forward hooks. Vector lookup is lens-structure dependent.

## Test command

```bash
pytest                 # 26 tests, no real model required
```

Tests use `TestClient` (FastAPI). They do not download models or lens files.

## Debugging

- `curl http://127.0.0.1:8787/api/health` confirms backend is up
- `curl http://127.0.0.1:8787/api/diagnostics` shows torch/jlens/config info
- Click **Diagnostics** in UI for a formatted view
- Backend logs include timing per request
- Do **not** log full prompts by default (privacy)

## `.internal/local_jlens_v3_agent_spec.md` and `.internal/local_jlens_v4_agent_spec.md`

These files document the intended behavior of every feature including acceptance criteria. Refer to them for detailed feature requirements.
