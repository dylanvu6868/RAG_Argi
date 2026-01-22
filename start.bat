@echo off
echo ========================================
echo RAG System - Quick Start
echo ========================================
echo.

echo Checking if Ollama is installed...
where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ollama found
) else (
    echo [WARNING] Ollama not found
    echo Please install Ollama from: https://ollama.ai
    echo After installation, run: ollama pull llama2
)

echo.
echo Starting Streamlit application...
echo.
echo The app will open at: http://localhost:8501
echo.
echo ========================================
echo Instructions:
echo 1. Select LLM Provider (Ollama or OpenAI)
echo 2. Click "Khoi dong he thong"
echo 3. Upload PDF files
echo 4. Ask questions about your documents
echo ========================================
echo.

streamlit run app.py
