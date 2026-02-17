up:
	docker compose up --build -d postgres redis ingestion analytics semantic alerting gateway

up-stream:
	docker compose --profile streaming up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f gateway ingestion analytics semantic alerting

seed:
	python scripts/seed_demo_data.py

train-models:
	python scripts/train_models.py

test:
	pytest -q
