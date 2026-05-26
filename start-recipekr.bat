@echo off
setlocal EnableExtensions DisableDelayedExpansion

REM Use UTF-8 for Korean text in this console window.
chcp 65001 >nul
set "JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8 %JAVA_TOOL_OPTIONS%"
set "DEBUG="

echo ========================================================
echo RecipeKR - local server launcher
echo ========================================================
echo.

REM Move to the directory where this batch file exists.
cd /d "%~dp0"

REM Load .env so the app can run without IDE-provided environment variables.
if exist ".env" (
    echo Loading environment variables from .env...
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" set "%%A=%%B"
    )
) else (
    echo .env was not found. Using application.yml defaults.
)

REM Default to the TiDB profile unless .env already defines a profile.
if not defined SPRING_PROFILES_ACTIVE set "SPRING_PROFILES_ACTIVE=tidb"

where java >nul 2>nul
if errorlevel 1 (
    echo.
    echo Java was not found. Please install JDK 21 and run this file again.
    echo Download: https://adoptium.net/temurin/releases/?version=21
    pause
    exit /b 1
)

if not exist "gradlew.bat" (
    echo.
    echo gradlew.bat was not found. Run this file from the project root.
    pause
    exit /b 1
)

echo.
echo Starting Spring Boot server. Profile: %SPRING_PROFILES_ACTIVE%
echo Please wait. The first build can take a while.
echo Open http://localhost:8080 after the server starts successfully.
echo.

REM Run the server through the Gradle wrapper.
call ".\gradlew.bat" bootRun --console=plain

echo.
echo Server stopped. If an error occurred, check the messages above.
pause
