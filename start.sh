#!/bin/bash
cd ~/job-tracker
source .venv/bin/activate
streamlit run dashboard/app.py --server.runOnSave true
