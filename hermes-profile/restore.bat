@echo off
REM ============================================================
REM restore.bat - 把 git 仓库里的 hermes-profile 恢复到 Hermes profile 目录
REM ============================================================
setlocal

set REPO_DIR=%~dp0
set PROFILE_DIR=%LOCALAPPDATA%\hermes\profiles\av-transcription

echo.
echo === 音视频转录 Agent - 恢复脚本 ===
echo 仓库目录:   %REPO_DIR%
echo 目标目录:   %PROFILE_DIR%
echo.

if not exist "%PROFILE_DIR%" (
    echo 创建目标目录: %PROFILE_DIR%
    mkdir "%PROFILE_DIR%" 2>nul
)

echo.
echo === 1. 复制 hermes-profile 文件 === ^
copy /Y "%REPO_DIR%hermes-profile\SOUL.md"             "%PROFILE_DIR%\SOUL.md" ^
copy /Y "%REPO_DIR%hermes-profile\config.yaml"        "%PROFILE_DIR%\config.yaml" ^
copy /Y "%REPO_DIR%hermes-profile\profile.yaml"       "%PROFILE_DIR%\profile.yaml" ^
copy /Y "%REPO_DIR%hermes-profile\.no-bundled-skills" "%PROFILE_DIR%\.no-bundled-skills"

echo.
echo === 2. 设置 .env === ^
if not exist "%PROFILE_DIR%\.env" (
    if exist "%REPO_DIR%.env.example" (
        copy /Y "%REPO_DIR%.env.example" "%PROFILE_DIR%\.env"
        echo 已复制 .env.example 到 .env，请编辑填入真实凭据：
        echo   notepad "%PROFILE_DIR%\.env"
    ) else (
        echo 警告：未找到 .env.example
    )
) else (
    echo .env 已存在，跳过
)

echo.
echo === 3. 收紧 .env 权限 ===
icacls "%PROFILE_DIR%\.env" /inheritance:r /grant:r "%USERNAME%:(R,W)" 2>nul

echo.
echo === 恢复完成 ===
echo 下一步：
echo   1) 编辑 %PROFILE_DIR%\.env 填入真实凭据
echo   2) 重启 gateway：
echo        taskkill /F /IM python.exe /FI "WINDOWTITLE eq *av-transcription*" 2^>nul
echo        cd /d "%PROFILE_DIR%"
echo        start /B cmd /c "hermes -p av-transcription gateway run -v"
echo.
endlocal
