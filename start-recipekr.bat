@echo off
chcp 65001 >nul
echo ========================================================
echo 냉장고 레시피 (RecipeKR) - 로컬 서버 실행 스크립트
echo ========================================================
echo.
echo TiDB 연결 프로필로 Spring Boot 서버를 시작합니다...
echo 시작 중입니다. 잠시만 기다려주세요. (초기 빌드 시 시간이 걸릴 수 있습니다)
echo 서버가 성공적으로 켜지면 브라우저에서 http://localhost:8080 으로 접속하세요!
echo.

:: 스크립트가 위치한 폴더로 이동 (탐색기에서 바로 실행 시 현재 경로 보장)
cd /d "%~dp0"

:: 로컬 테스트용 TiDB 프로필 강제 지정
set SPRING_PROFILES_ACTIVE=tidb

:: Gradle을 이용해 서버 실행 (call을 사용하여 실행 후 아래 명령어로 돌아오게 함)
call gradlew.bat bootRun

echo.
echo 서버가 종료되었습니다. 오류가 발생했다면 위 메시지를 확인해주세요.
pause
