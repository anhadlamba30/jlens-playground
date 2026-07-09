.PHONY: run backend frontend install-ui install-deps list-lenses diagnostics setup-config test

run:
	./run.sh

backend:
	cd backend && python -m app.main

frontend:
	cd frontend && npm run dev

install-ui:
	cd frontend && npm install

install-deps:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

list-lenses:
	python scripts/list_hf_lenses.py

diagnostics:
	curl http://127.0.0.1:8787/api/diagnostics

setup-config:
	python scripts/setup_config.py

test:
	pytest
