@echo off
REM SmartBuy - one-click setup and run for Windows
cd /d "%~dp0"
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Installing / checking dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

if not exist models\metrics.json (
    echo Training the ML models for the first time - takes 2-4 minutes...
    python train.py
)

echo Starting SmartBuy at http://localhost:8501
python -m streamlit run app.py
