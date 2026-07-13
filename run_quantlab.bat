@echo off
echo ===================================================
echo   QuantLab Financial Terminal Startup Script
echo ===================================================
echo.
echo Launching browser interface...
start "" "http://localhost:8501"
echo.
echo Starting Streamlit backend server...
streamlit run Home.py
pause
