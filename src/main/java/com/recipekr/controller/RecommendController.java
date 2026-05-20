package com.recipekr.controller;

import com.recipekr.service.AiRecommendService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;
import java.util.Map;

/**
 * RecommendController - 레시피 추천 요청 처리 컨트롤러
 */
@Controller
@RequiredArgsConstructor
@RequestMapping("/recipe")
public class RecommendController {

    private final AiRecommendService aiRecommendService;

    /** 추천 입력 폼 페이지 */
    @GetMapping("/recommend")
    public String recommendForm() {
        return "recipe/recommend";
    }

    /** 추천 결과 처리 */
    @PostMapping("/recommend")
    public String recommend(
            @RequestParam("ingredients")  String ingredients,
            @RequestParam("health_type")  String healthType,
            @RequestParam(value = "top_n", defaultValue = "3") int topN,
            Model model) {

        List<Map<String, Object>> results =
                aiRecommendService.recommend(ingredients, healthType, topN);

        model.addAttribute("results",     results);
        model.addAttribute("ingredients", ingredients);
        model.addAttribute("healthType",  healthType);
        return "recipe/result";
    }
}
