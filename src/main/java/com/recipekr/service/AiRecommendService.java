package com.recipekr.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * AiRecommendService - Spring Boot ↔ Python 연동 서비스
 * -------------------------------------------------------
 * ProcessBuilder를 통해 python-ai/predict.py를 실행하고,
 * 표준 출력(stdout)으로 반환된 JSON을 파싱하여 반환합니다.
 *
 * [주의] 한글 인코딩 방지를 위해 StandardCharsets.UTF_8로 처리합니다.
 */
@Slf4j
@Service
public class AiRecommendService {

    private final ObjectMapper objectMapper = new ObjectMapper();

    private String getPythonExecutable() {
        String condaPath = "C:\\Users\\whyei\\anaconda3\\envs\\conda_venv\\python.exe";
        if (new java.io.File(condaPath).exists()) {
            return condaPath;
        }
        return "python";
    }

    /**
     * Python 추천 스크립트를 실행하여 레시피 추천 결과를 반환합니다.
     *
     * @param ingredients 쉼표로 구분된 재료 문자열 (예: "계란,양파,감자")
     * @param healthType  건강 유형 (예: "다이어트", "당뇨", "저염식", "일반")
     * @param topN        추천 결과 개수
     * @return 추천 결과 맵 (recommendations 리스트, ai_message 포함)
     */
    public Map<String, Object> recommend(String ingredients, String healthType, int topN) {
        try {
            // ① predict.py 경로 계산 (프로젝트 루트 기준)
            Path scriptPath = Paths.get(System.getProperty("user.dir"))
                    .resolve("python-ai")
                    .resolve("predict.py")
                    .toAbsolutePath();

            log.info("[AI] Python 실행: {}", scriptPath);

            // ② ProcessBuilder 설정
            ProcessBuilder pb = new ProcessBuilder(
                    getPythonExecutable(),
                    scriptPath.toString(),
                    "--ingredients", ingredients,
                    "--health_type",  healthType,
                    "--top_n",        String.valueOf(topN)
            );
            pb.redirectErrorStream(false); // stderr는 별도 처리

            // ③ Windows 환경에서 Python stdout UTF-8 강제 설정 (한글 깨짐 방지 핵심)
            pb.environment().put("PYTHONIOENCODING", "utf-8");
            pb.environment().put("PYTHONUTF8", "1");
            
            // GEMINI_API_KEY 환경변수 전달 (시스템 → .env 파일 폴백)
            String geminiApiKey = System.getenv("GEMINI_API_KEY");
            if (geminiApiKey == null || geminiApiKey.isBlank()) {
                // .env 파일에서 직접 읽기 (절대 경로 고정)
                try {
                    Path envPath = Paths.get("D:/git/202605/recipekr/.env");
                    if (envPath.toFile().exists()) {
                        for (String envLine : java.nio.file.Files.readAllLines(envPath)) {
                            if (envLine.startsWith("GEMINI_API_KEY=")) {
                                geminiApiKey = envLine.substring("GEMINI_API_KEY=".length()).trim();
                                break;
                            }
                        }
                    }
                } catch (Exception ex) {
                    log.warn("[AI] .env 파일 읽기 실패: {}", ex.getMessage());
                }
            }
            if (geminiApiKey != null && !geminiApiKey.isBlank()) {
                pb.environment().put("GEMINI_API_KEY", geminiApiKey);
            } else {
                log.warn("[AI] GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다!");
            }

            // ④ 프로세스 실행
            Process process = pb.start();

            // ④ stdout (JSON 결과) 읽기 - UTF-8 강제 적용으로 한글 깨짐 방지
            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line);
                }
            }

            // ⑤ stderr 로그 출력 (디버깅용)
            StringBuilder errOutput = new StringBuilder();
            try (BufferedReader errReader = new BufferedReader(
                    new InputStreamReader(process.getErrorStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = errReader.readLine()) != null) {
                    errOutput.append(line).append("\n");
                }
            }
            if (!errOutput.isEmpty()) {
                log.warn("[AI] Python stderr:\n{}", errOutput);
            }

            int exitCode = process.waitFor();
            log.info("[AI] Python 종료 코드: {}", exitCode);

            // ⑥ 에러 JSON 응답 처리 {"error": "..."}
            String json = output.toString().trim();
            if (json.startsWith("{\"error\"")) {
                Map<String, Object> err = objectMapper.readValue(json, new TypeReference<>() {});
                log.error("[AI] Python 에러 응답: {}", err.get("error"));
                return Collections.emptyMap();
            }

            // ⑦ 정상 JSON 객체 파싱 (recommendations, ai_message 포함)
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});

        } catch (Exception e) {
            log.error("[AI] 추천 스크립 실행 실패: {}", e.getMessage(), e);
            return Collections.emptyMap();
        }
    }
}
