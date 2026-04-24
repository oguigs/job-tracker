.PHONY: run pipeline backup test clean

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
	cd ~/job-tracker && source .venv/bin/activate && python -m py_compile dashboard/views/*.py dashboard/components.py main.py
	echo "Sem erros de sintaxe!"

prefect:
	cd ~/job-tracker && source .venv/bin/activate && python pipeline_prefect.py

prefect-serve:
	cd ~/job-tracker && source .venv/bin/activate && python pipeline_prefect.py --serve

prefect-ui:
	cd ~/job-tracker && source .venv/bin/activate && prefect server start
