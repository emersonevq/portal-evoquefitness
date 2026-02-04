@echo off
echo.
echo ========================================
echo   Portal Evoque - Dev Environment
echo ========================================
echo.

echo Iniciando Backend (porta 3001)...
start "Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 3001 --reload"

timeout /t 3 /nobreak

echo Iniciando Frontend (porta 3005)...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Servidores iniciados!
echo ========================================
echo.
echo Frontend:        http://localhost:3005
echo Backend API:     http://localhost:3001
echo Backend Docs:    http://localhost:3001/docs
echo.
echo Feche as janelas para parar os servidores.
echo.
pause
