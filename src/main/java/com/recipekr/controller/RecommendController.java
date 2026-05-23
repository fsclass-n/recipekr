package com.recipekr.controller;

import com.recipekr.service.AiRecommendService;
import com.recipekr.repository.DiscountItemRepository;
import com.recipekr.domain.DiscountItem;
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
    private final DiscountItemRepository discountItemRepository;

    /** 추천 입력 폼 페이지 (냉장고 UI) */
    @GetMapping("/recommend")
    public String recommendForm(Model model) {
        List<DiscountItem> todayItems = discountItemRepository.findTodayItems();
        java.util.Collections.shuffle(todayItems);

        // 카테고리 분류: 고기류(왼쪽 문), 채소·과일(오른쪽 문), 기타(안쪽)
        List<String> meatFishKeywords = List.of("고기", "돈육", "우육", "계육", "닭", "소", "돼지", 
                "삼겹살", "목살", "갈비", "한우", "생선", "고등어", "연어", "오징어", "새우", "참치", "오리", "치킨");
        
        // 채소 및 야채 키워드 (중앙 내부)
        List<String> veggieKeywords = List.of("배추", "무", "양파", "파", "마늘", "생강", "양배추", "채소", "야채", 
                "샐러드", "상추", "깻잎", "당근", "감자", "고구마", "오이", "버섯");

        // 제외 키워드 (비식품, 펫용품, 잘못 크롤링된 텍스트, 브랜드명 등)
        List<String> excludeKeywords = List.of("펫", "강아지", "개", "고양이", "사료", "껌", 
                "보약", "패드", "물티슈", "세제", "샴푸", "바디", "치약", "휴지", "기저귀", "thepet", "배변",
                "순위", "하락", "광고", "툴팁", "프라임", "호밀", "레모나", 
                "제일제당", "피코크", "압도적", "더독", "오마이트릿", "더 독", "노브랜드", "jaju");

        java.util.List<DiscountItem> meatItems = new java.util.ArrayList<>(); // 왼쪽문 (frozenItems에 매핑됨)
        java.util.List<DiscountItem> others = new java.util.ArrayList<>();    // 중앙내부 (otherItems에 매핑됨)
        java.util.List<DiscountItem> rightItems = new java.util.ArrayList<>();// 오른쪽문 (freshItems에 매핑됨)

        for (DiscountItem item : todayItems) {
            String name = (item.getProductName() + " " +
                    (item.getIngredientName() != null ? item.getIngredientName() : "")).toLowerCase();
            
            // 제외 키워드가 포함된 상품은 스킵
            boolean shouldExclude = false;
            for (String ex : excludeKeywords) {
                if (name.contains(ex)) { shouldExclude = true; break; }
            }
            if (shouldExclude) continue;

            boolean matched = false;
            if (meatItems.size() < 6) {
                for (String kw : meatFishKeywords) {
                    if (name.contains(kw)) { meatItems.add(item); matched = true; break; }
                }
            }
            if (!matched && others.size() < 6) {
                for (String kw : veggieKeywords) {
                    if (name.contains(kw)) { others.add(item); matched = true; break; }
                }
            }
            // 남는 것(과일 등 기타)은 오른쪽 문으로
            if (!matched && rightItems.size() < 6) { 
                rightItems.add(item);
            }
        }

        model.addAttribute("frozenItems", meatItems);   // 왼쪽 문 = 고기류
        model.addAttribute("freshItems", rightItems);   // 오른쪽 문 = 과일·기타
        model.addAttribute("otherItems", others);        // 안쪽 = 채소·야채
        model.addAttribute("discountItems", todayItems); // 전체(하위호환)
        return "recipe/recommend";
    }

    /** 추천 결과 처리 */
    @PostMapping("/recommend")
    public String recommend(
            @RequestParam("ingredients")  String ingredients,
            @RequestParam("health_type")  String healthType,
            @RequestParam(value = "top_n", defaultValue = "3") int topN,
            Model model) {

        Map<String, Object> aiResult = aiRecommendService.recommend(ingredients, healthType, topN);

        Object recommendations = aiResult.getOrDefault("recommendations", List.of());
        Object aiMessage = aiResult.get("ai_message");

        model.addAttribute("results",     recommendations);
        model.addAttribute("aiMessage",   aiMessage);
        model.addAttribute("ingredients", ingredients);
        model.addAttribute("healthType",  healthType);
        return "recipe/result";
    }
}
