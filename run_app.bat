@echo off
echo ===================================================
echo Starting Smart Ration and Distribution System
echo ===================================================
echo Clearing cached bytecode...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo Launching Streamlit Server...
python -m streamlit run app.py
pause

