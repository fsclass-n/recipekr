# Stage 10 Summary: IDE 없이 RecipeKR 실행 가능하도록 배치 파일 안정화

## 작업 배경

`start-recipekr.bat`를 통해 VSCode/IntelliJ 같은 IDE 없이 프로젝트를 실행하려고 했지만, Windows 명령 프롬프트에서 한글이 깨지면서 배치 파일의 일부 줄이 잘못된 명령어로 해석되어 실행이 실패했다.

주요 증상은 다음과 같았다.

- 명령창에서 한글 문구가 깨져 표시됨
- `'IDE' is not recognized as an internal or external command` 같은 오류 발생
- 배치 파일의 한글 주석/문구가 `cmd.exe`에서 명령어처럼 잘못 해석됨
- IDE가 자동으로 넣어주던 환경변수가 없으면 DB/API 설정이 적용되지 않을 수 있음

## 원인

기존 `start-recipekr.bat`는 파일 안에 한글 `echo`와 한글 주석이 포함되어 있었고, 파일 시작 부분에서 `chcp 65001`로 UTF-8 코드페이지를 설정하고 있었다.

하지만 Windows `cmd.exe`는 배치 파일을 읽는 시점에 이미 현재 코드페이지 기준으로 파일 내용을 파싱한다. 따라서 `chcp 65001`이 실행되기 전에 UTF-8 한글 줄이 먼저 깨져 해석되었고, 그 결과 깨진 문자열 일부가 명령어로 실행되면서 오류가 발생했다.

또한 Spring Boot 설정에서는 콘솔 로그 인코딩이 `MS949`로 지정되어 있었는데, 배치 파일은 UTF-8 콘솔을 사용하도록 설정하고 있어 로그 인코딩도 서로 맞지 않았다.

## 변경 내역

### 1. `start-recipekr.bat` 수정

배치 파일이 어떤 Windows 코드페이지에서도 안전하게 파싱되도록 파일 내부 문구와 주석을 ASCII 기반으로 정리했다.

적용한 주요 변경 사항:

- `setlocal EnableExtensions DisableDelayedExpansion` 추가
- 콘솔 코드페이지를 UTF-8로 설정
- JVM 인코딩 옵션 추가
  - `-Dfile.encoding=UTF-8`
  - `-Dstdout.encoding=UTF-8`
  - `-Dstderr.encoding=UTF-8`
- `.env` 파일 자동 로드 기능 추가
- `SPRING_PROFILES_ACTIVE`가 없으면 기본값을 `tidb`로 설정
- `java` 명령 사용 가능 여부 확인
- `gradlew.bat` 존재 여부 확인
- Gradle wrapper를 통해 `bootRun --console=plain` 실행
- `DEBUG` 환경변수로 인해 Gradle wrapper 명령이 과도하게 출력되는 현상 방지

수정 파일:

- `start-recipekr.bat`

### 2. Spring Boot 콘솔 인코딩 수정

`src/main/resources/application.yml`의 콘솔 로그 인코딩을 배치 파일의 UTF-8 설정과 맞췄다.

변경 전:

```yml
logging:
  charset:
    console: MS949
    file: UTF-8
```

변경 후:

```yml
logging:
  charset:
    console: UTF-8
    file: UTF-8
```

수정 파일:

- `src/main/resources/application.yml`

## 실행 방법

IDE 없이 Windows 탐색기 또는 명령 프롬프트에서 바로 실행할 수 있다.

### 방법 1. 탐색기에서 실행

1. 프로젝트 폴더를 연다.
   - `D:\wi\lab\recipekr`
2. `start-recipekr.bat` 파일을 더블클릭한다.
3. 명령 프롬프트 창이 열리면 서버가 시작될 때까지 기다린다.
4. 브라우저에서 아래 주소로 접속한다.

```text
http://localhost:8080
```

### 방법 2. 명령 프롬프트에서 실행

```bat
cd /d D:\wi\lab\recipekr
start-recipekr.bat
```

## 실행 전 필요 조건

### 1. JDK 21 설치

프로젝트는 Gradle toolchain에서 Java 21을 사용한다. 실행 PC에 JDK 21이 설치되어 있어야 한다.

확인 명령:

```bat
java -version
```

JDK가 없으면 아래 주소에서 JDK 21을 설치한다.

```text
https://adoptium.net/temurin/releases/?version=21
```

### 2. `.env` 파일 확인

프로젝트 루트에 `.env` 파일이 있으면 `start-recipekr.bat`가 자동으로 읽어서 환경변수로 등록한다.

현재 배치 파일은 다음과 같은 값을 `.env`에서 읽어 사용할 수 있다.

```text
SPRING_PROFILES_ACTIVE
TIDB_URL
TIDB_USERNAME
TIDB_PASSWORD
GEMINI_API_KEY
```

`.env`가 없더라도 `application.yml`과 `application-tidb.yml`의 기본값으로 실행을 시도한다.

## 검증 결과

수정 후 다음 항목을 확인했다.

- `cmd.exe`에서 `start-recipekr.bat` 실행 시 한글 깨짐으로 인한 명령어 오류가 더 이상 발생하지 않음
- Gradle wrapper 정상 실행 확인
- Spring Boot 서버가 `localhost:8080`에서 LISTEN 상태로 기동됨
- `http://localhost:8080` 요청에 HTTP `200` 응답 확인
- `git diff --check`로 공백/패치 형식 문제 없음 확인

## 종료 방법

서버가 실행 중인 명령 프롬프트 창에서 아래 방법 중 하나로 종료한다.

- `Ctrl + C` 입력 후 종료 확인
- 명령 프롬프트 창 닫기

## 참고

배치 파일 내부에 한글 문구를 다시 추가하면 Windows 코드페이지에 따라 같은 문제가 재발할 수 있다. 한글 안내 문구가 필요하면 별도 `README` 또는 Markdown 문서에 작성하고, `.bat` 파일 안에는 ASCII 문구만 유지하는 것이 안전하다.
