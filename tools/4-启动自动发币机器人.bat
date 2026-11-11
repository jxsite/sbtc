@echo off
chcp 65001 >nul
title SBTC 24小时无人值守跨链自动发币机器人
cd /d %~dp0

echo =======================================================
echo    SBTC 跨链自动发币机器人 (24小时无人值守)
echo    监控 BSC 链上 USDT 入账 -> 自动向买家发货 SBTC
echo =======================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [错误] 未检测到 Python 环境，请先安装 Python 3！
  pause
  exit /b 1
)

python sbtc_auto_trader.py
pause
