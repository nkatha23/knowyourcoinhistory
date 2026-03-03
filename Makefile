.PHONY: dev-backend dev-frontend test lint format typecheck clean

dev-backend:
	source .venv/bin/activate && python main.py

dev-frontend:
	cd web && npm run dev

test:
	source .venv/bin/activate && pytest tests/ -v --cov=kycc

lint:
	source .venv/bin/activate && ruff check kycc/ tests/

format:
	source .venv/bin/activate && black kycc/ tests/

typecheck:
	source .venv/bin/activate && mypy kycc/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete
