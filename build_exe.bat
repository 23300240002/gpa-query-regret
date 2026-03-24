@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo [ERROR] 未找到 .venv\Scripts\python.exe
  echo 请先创建并激活虚拟环境，再安装依赖。
  pause
  exit /b 1
)

echo [1/2] 安装打包工具...
.venv\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 goto :fail

echo [2/2] 开始打包 exe...
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name GPAQueryRegret --add-data "templates;templates" web_app.py
if errorlevel 1 goto :fail

echo 打包完成，exe 位置：dist\GPAQueryRegret.exe
pause
exit /b 0

:fail
echo 打包失败，请检查上方日志。
pause
exit /b 1
