# 1단계: 빌드 환경 설정 (Java 21 및 Gradle 사용)
FROM gradle:8.5-jdk21 AS build
WORKDIR /app

# 소스 코드를 모두 복사
COPY . .

# Gradle을 사용하여 애플리케이션 빌드 (테스트는 생략하여 배포 속도 향상)
RUN ./gradlew clean build -x test

# 2단계: 실행 환경 설정 (가벼운 JRE 환경 사용)
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

# 빌드 단계에서 생성된 JAR 파일을 복사
COPY --from=build /app/build/libs/*.jar app.jar

# Render는 동적으로 PORT 환경변수를 할당하므로, 기본값을 8080으로 두고 이를 사용
ENV PORT=8080
EXPOSE $PORT

# Spring Boot 실행 명령어 (Render에서 제공하는 PORT 환경변수를 서버 포트로 지정)
ENTRYPOINT ["sh", "-c", "java -Dserver.port=${PORT} -jar app.jar"]
