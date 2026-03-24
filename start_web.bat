@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo [ERROR] 未找到虚拟环境解释器: .venv\Scripts\python.exe
  echo 请先在项目目录创建并配置 .venv。
  pause
  exit /b 1
)
.venv\Scripts\python.exe web_app.py
