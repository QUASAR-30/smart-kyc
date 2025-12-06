#!/bin/bash
# Explicitly use the python/uvicorn from the local venv
./venv/bin/uvicorn app.main:app --port 8000 --reload
