.PHONY: help setup dev backend frontend download-data update-data prepare-data create-labels train evaluate retrain test lint clean

help:
	@echo "SIH26079: AI-Based Forecast Bust Detection Platform"
	@echo "Available commands:"
	@echo "  make setup          - Install dependencies and initialize environment"
	@echo "  make dev            - Run backend and dashboard development servers"
	@echo "  make backend        - Run FastAPI backend server"
	@echo "  make download-data  - Run the automated dataset downloader CLI"
	@echo "  make update-data    - Run incremental dataset updater"
	@echo "  make prepare-data   - Run data validation and quality check report"
	@echo "  make create-labels  - Run configurable forecast bust labeling"
	@echo "  make train          - Train, calibrate, and evaluate ML bust prediction models"
	@echo "  make evaluate       - Run detailed model evaluation & calibration metrics"
	@echo "  make retrain        - Trigger automated retraining & promotion pipeline"
	@echo "  make test           - Run full test suite (backend, pipeline, ML leakage)"

setup:
	python -m pip install -r requirements.txt
	python -m scripts.setup_data

dev:
	python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

backend:
	python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

download-data:
	python -m data_pipeline.download --region india --source demo

update-data:
	python -m data_pipeline.update

prepare-data:
	python -m data_pipeline.quality

create-labels:
	python -m data_pipeline.labeler

train:
	python -m ml_pipeline.train

evaluate:
	python -m ml_pipeline.evaluate

retrain:
	python -m ml_pipeline.auto_retrain

test:
	pytest tests/ -v
