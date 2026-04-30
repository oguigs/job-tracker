.PHONY: run pipeline backup test clean lint format dbt-run dbt-test dbt-docs dbt-all

run:
	cd ~/job-tracker && source .venv/bin/activate && streamlit run dashboard/app.py

pipeline:
	cd ~/job-tracker && source .venv/bin/activate && python main.py

backup:
	cd ~/job-tracker && source .venv/bin/activate && python -c "from database.schemas import fazer_backup; fazer_backup()"

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

lint:
	cd ~/job-tracker && source .venv/bin/activate && ruff check .

format:
	cd ~/job-tracker && source .venv/bin/activate && ruff format .

dbt-run:
	cd ~/job-tracker && source dbt/.venv/bin/activate && dbt run --project-dir dbt/ --profiles-dir dbt/

dbt-test:
	cd ~/job-tracker && source dbt/.venv/bin/activate && dbt test --project-dir dbt/ --profiles-dir dbt/

dbt-docs:
	cd ~/job-tracker && source dbt/.venv/bin/activate && dbt docs generate --project-dir dbt/ --profiles-dir dbt/ && dbt docs serve --project-dir dbt/ --profiles-dir dbt/ --port 8080

dbt-all: dbt-run dbt-test

prefect:
	cd ~/job-tracker && source .venv/bin/activate && python pipeline_prefect.py

prefect-serve:
	cd ~/job-tracker && source .venv/bin/activate && python pipeline_prefect.py --serve

prefect-ui:
	cd ~/job-tracker && source .venv/bin/activate && prefect server start
