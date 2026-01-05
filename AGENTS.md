# AGENTS.md

## Dev environment tips
- Create virtual environment: `python -m venv venv`
- Activate: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
- Install dependencies: `pip install -r requirements.txt`
- Run server: `uvicorn src.main:app --reload`
- Store generated artefacts in `.context/` so reruns stay deterministic.

## Testing instructions
- Execute `pytest tests/ -v` to run the test suite.
- Run single test file: `pytest tests/services/test_lead_crud.py -v`
- With coverage: `pytest tests/ -v --cov=src --cov-report=html`
- Run `ruff check src/ tests/ && pytest tests/ -v` before opening a PR to mimic CI.
- Add or update tests alongside any service or agent changes.

## PR instructions
- Follow Conventional Commits (for example, `feat(agent): add upsell suggestions`).
- Update relevant docs in `documentation/` and `.context/docs/` when behaviour shifts.
- Attach sample output or test results when functionality changes.
- Run `ruff format src/ tests/` before committing.

## Repository map
- `documentation/` — explain what lives here and when agents should edit it.
- `prompts/` — explain what lives here and when agents should edit it.

## AI Context References
- Documentation index: `.context/docs/README.md`
- Agent playbooks: `.context/agents/README.md`
- Contributor guide: `CONTRIBUTING.md`
