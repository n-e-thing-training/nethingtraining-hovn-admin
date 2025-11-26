Write-Host "Installing dependencies..."
pip install -r requirements.txt

Write-Host "Installing Playwright browsers..."
python -m playwright install

Write-Host "Starting FastAPI admin server on http://localhost:8000 ..."
uvicorn admin_app:app --host 0.0.0.0 --port 8000 --reload
