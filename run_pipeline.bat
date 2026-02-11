@echo off
REM Run the NeuralStack multi-agent article pipeline from a double-click.
cd /d "%~dp0"
python scripts\run_pipeline.py
REM Run from content-pipeline folder so PROJECT_ROOT is correct.
echo.
echo Multi-agent pipeline run finished. Press any key to close this window.
pause >nul

