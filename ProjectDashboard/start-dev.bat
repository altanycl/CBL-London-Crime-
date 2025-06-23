@echo off
echo Starting London Crime Dashboard Development Environment

echo Starting backend server...
start cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python map_api.py"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo Starting frontend server...
start cmd /k "npm run dev"

echo Development environment started!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000 