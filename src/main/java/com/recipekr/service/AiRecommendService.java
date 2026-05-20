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

    /**
     * Python 추천 스크립트를 실행하여 레시피 추천 결과를 반환합니다.
     *
     * @param ingredients 쉼표로 구분된 재료 문자열 (예: "계란,양파,감자")
     * @param healthType  건강 유형 (예: "다이어트", "당뇨", "저염식", "일반")
     * @param topN        추천 결과 개수
     * @return 추천 레시피 목록 (JSON → Map 리스트)
     */
    public List<Map<String, Object>> recommend(String ingredients, String healthType, int topN) {
        try {
            // ① predict.py 경로 계산 (프로젝트 루트 기준)
            Path scriptPath = Paths.get(System.getProperty("user.dir"))
                    .resolve("python-ai")
                    .resolve("predict.py")
                    .toAbsolutePath();

            log.info("[AI] Python 실행: {}", scriptPath);

            // ② ProcessBuilder 설정
            ProcessBuilder pb = new ProcessBuilder(
                    "python",
                    scriptPath.toString(),
                    "--ingredients", ingredients,
                    "--health_type",  healthType,
                    "--top_n",        String.valueOf(topN)
            );
            pb.redirectErrorStream(false); // stderr는 별도 처리

            // ③ Windows 환경에서 Python stdout UTF-8 강제 설정 (한글 깨짐 방지 핵심)
            pb.environment().put("PYTHONIOENCODING", "utf-8");
            pb.environment().put("PYTHONUTF8", "1");

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
                return Collections.emptyList();
            }

            // ⑦ 정상 JSON 배열 파싱
            return objectMapper.readValue(json, new TypeReference<List<Map<String, Object>>>() {});

        } catch (Exception e) {
            log.error("[AI] 추천 스크립트 실행 실패: {}", e.getMessage(), e);
            return Collections.emptyList();
        }
    }
}
