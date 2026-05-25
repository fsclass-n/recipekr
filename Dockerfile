# 1단계: 빌드 환경 설정 (Java 21 및 Gradle 사용)
FROM gradle:8.5-jdk21 AS build
WORKDIR /app

# 소스 코드를 모두 복사
COPY . .

# 권한 문제 해결 후 빌드 (테스트는 생략)
RUN chmod +x ./gradlew
RUN ./gradlew clean build -x test

# 2단계: 실행 환경 설정 (Java 21 + Python 3 통합 환경)
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app

# 시스템 파이썬 및 필수 도구 설치
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv wget fonts-nanum && \
    rm -rf /var/lib/apt/lists/*

# 파이썬 가상환경 생성 (이후 파이썬 명령어는 모두 이 가상환경을 사용)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# requirements.txt 복사 및 파이썬 패키지 설치
COPY python-ai/requirements.txt ./python-ai/
RUN pip install --no-cache-dir -r python-ai/requirements.txt

# RPA 크롤러를 위한 Playwright 브라우저 및 필수 의존성 설치
RUN playwright install --with-deps chromium

# 모든 파이썬 스크립트 복사
COPY python-ai/ ./python-ai/

# 빌드 단계에서 생성된 Spring Boot JAR 파일을 복사
COPY --from=build /app/build/libs/*.jar app.jar

# Render는 동적으로 PORT 환경변수를 할당하므로, 기본값을 8080으로 설정
ENV PORT=8080
EXPOSE $PORT

# Spring Boot 실행 명령어 (JAVA_OPTS를 통해 외부에서 JVM 옵션을 동적으로 조절 가능하도록 수정)
ENV JAVA_OPTS="-Xms128m -Xmx256m"
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -Dserver.port=${PORT} -jar app.jar"]
