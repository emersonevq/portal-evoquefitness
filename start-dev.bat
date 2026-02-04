@echo off
REM Script para iniciar Frontend e Backend simultaneamente (Windows)
REM Frontend: porta 3005
REM Backend: porta 3001

setlocal enabledelayedexpansion

REM Cores não funcionam bem no Windows, usar texto simples
echo ========================================
echo Portal Evoque - Dev Environment (Windows)
echo ========================================
echo.

REM Validar que estamos na raiz do projeto
if not exist "package.json" (
    echo Erro: Este script deve ser executado da raiz do projeto
    echo Estrutura esperada:
    echo   - package.json (na raiz)
    echo   - backend/main.py (backend FastAPI)
    echo   - frontend/package.json (frontend React)
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo Erro: Pasta frontend ou frontend/package.json nao encontrada
    pause
    exit /b 1
)

if not exist "backend\main.py" (
    echo Erro: Arquivo backend/main.py nao encontrado
    pause
    exit /b 1
)

REM Criar arquivo .env se não existir
if not exist ".env" (
    echo Criando arquivo .env...
    (
        echo # Backend Configuration
        echo VITE_API_BASE=/api
        echo VITE_PROXY_TARGET=http://127.0.0.1:3001
    ) > .env
    echo Arquivo .env criado
)

echo.
echo ========================================
echo Iniciando Backend
echo ========================================
echo Porta: 3001
echo Tecnologia: FastAPI + Uvicorn
echo.

REM Iniciar backend em nova janela
start "Backend - Evoque Portal" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 3001 --reload"

REM Aguardar um pouco para o backend inicializar
timeout /t 3 /nobreak

echo.
echo ========================================
echo Iniciando Frontend
echo ========================================
echo Porta: 3005
echo Tecnologia: React + Vite
echo.

REM Iniciar frontend em nova janela
start "Frontend - Evoque Portal" cmd /k "cd frontend && npm run dev"

REM Aguardar um pouco para confirmação
timeout /t 2 /nobreak

echo.
echo ========================================
echo Status dos Servidores
echo ========================================
echo Frontend: http://localhost:3005
echo Backend API: http://localhost:3001
echo Backend Docs: http://localhost:3001/docs
echo.
echo Pressione Ctrl+C em qualquer janela para parar o servidor
echo.
pause
