@echo off
REM Run the NeuralStack multi-agent pipeline using a local Ollama model.
cd /d "%~dp0"
REM Run from content-pipeline folder.

REM Configure LLM backend for this session only.
set NEURALSTACK_LLM_BACKEND=ollama
set NEURALSTACK_OLLAMA_MODEL=qcwind/qwen3-8b-instruct-Q4-K-M

echo Using NEURALSTACK_LLM_BACKEND=%NEURALSTACK_LLM_BACKEND%
echo Using NEURALSTACK_OLLAMA_MODEL=%NEURALSTACK_OLLAMA_MODEL%
echo.

python scripts\run_pipeline.py
echo.
echo Ollama-backed multi-agent pipeline run finished. Press any key to close this window.
pause >nul

