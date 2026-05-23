import os

html_content = r"""<!DOCTYPE html>
<html lang="ko" xmlns:th="http://www.thymeleaf.org" xmlns:sec="http://www.thymeleaf.org/extras/spring-security">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 레시피 추천 | 냉장고 레시피</title>
    <link rel="icon" type="image/svg+xml" href="/images/favicon.svg">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" th:href="@{/css/global.css}">
    <style>
        html, body { overflow-x: hidden; }

        .fridge-container { max-width: 800px; margin: 40px auto 0; position: relative; perspective: 3000px; }

        .fridge-wrapper {
            background: #0f172a; border-radius: 8px; padding: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            position: relative; border: 4px solid #334155;
            height: 65vh; min-height: 500px; max-height: 650px;
            transform-style: preserve-3d;
        }

        /* ── 양문 3D ── */
        .fridge-door { position: absolute; top: 0; bottom: 0; width: 50%; z-index: 10; perspective: 2000px; pointer-events: none; }
        .left-door { left: 0; }
        .right-door { right: 0; }

        .door-inner {
            position: absolute; top: 0; bottom: 0; left: 0; right: 0;
            transition: transform 1.2s cubic-bezier(0.2, 0.9, 0.3, 1.1);
            transform-style: preserve-3d; pointer-events: auto;
        }
        .left-door .door-inner { transform-origin: left; }
        .right-door .door-inner { transform-origin: right; }
        .left-door.open .door-inner { transform: rotateY(-140deg); }
        .right-door.open .door-inner { transform: rotateY(140deg); }

        .door-open-overlay { position: absolute; top: 0; bottom: 0; left: 0; right: 0; cursor: pointer; z-index: 20; }
        .left-door.open .door-open-overlay, .right-door.open .door-open-overlay { display: none; }

        .door-front, .door-back {
            position: absolute; top: 0; bottom: 0; width: 100%;
            backface-visibility: hidden; display: flex; align-items: center; justify-content: center;
        }
        
        .door-front {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 30%, #f1f5f9 70%, #cbd5e1 100%);
            border: 1px solid #94a3b8; flex-direction: column;
            box-shadow: inset 1px 0 3px rgba(255,255,255,0.9), inset -1px 0 3px rgba(0,0,0,0.1);
        }
        .left-door .door-front { border-radius: 8px 0 0 8px; border-right: 1px solid #64748b; }
        .right-door .door-front { border-radius: 0 8px 8px 0; border-left: 1px solid #64748b; }

        .door-back {
            background: #f1f5f9; transform: rotateY(180deg); border: 1px solid #cbd5e1;
            flex-direction: column; justify-content: flex-start;
            padding: 15px 25px 0 25px; box-shadow: inset 0 0 15px rgba(0,0,0,0.15);
        }
        .left-door .door-back { border-radius: 0 8px 8px 0; }
        .right-door .door-back { border-radius: 8px 0 0 8px; }

        .fridge-door-handle {
            position: absolute; top: 50%; transform: translateY(-50%); width: 8px; height: 160px;
            background: linear-gradient(to right, #e2e8f0, #ffffff, #cbd5e1); border-radius: 4px;
            box-shadow: 2px 0 4px rgba(0,0,0,0.1), inset 1px 0 2px rgba(255,255,255,0.9); border: 1px solid #94a3b8;
        }
        .left-door .fridge-door-handle { right: 20px; }
        .right-door .fridge-door-handle { left: 20px; box-shadow: -2px 0 4px rgba(0,0,0,0.1); }

        .home-bar {
            position: absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);
            width: 65%; height: 28%; border: 2px solid #cbd5e1; border-radius: 6px;
            background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.05), 0 1px 2px rgba(255,255,255,0.8);
        }
        .home-bar::after {
            content: ''; position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
            width: 40px; height: 4px; background: #94a3b8; border-radius: 2px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.2);
        }

        .door-guard-shelf {
            width: calc(100% + 50px); margin-left: -25px; margin-right: -25px; height: 50px; margin-top: auto;
            background: linear-gradient(to bottom, rgba(255,255,255,0.8), rgba(226,232,240,0.6));
            border-top: 2px solid rgba(255,255,255,1); border-bottom: 1px solid #cbd5e1;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05), inset 0 5px 10px rgba(255,255,255,0.5);
            cursor: pointer; position: relative; z-index: 15;
            display: flex; align-items: center; justify-content: center;
        }
        .door-guard-shelf:hover { background: linear-gradient(to bottom, rgba(255,255,255,0.9), rgba(226,232,240,0.8)); }
        .door-guard-shelf::before {
            content: ''; position: absolute; top: 4px; left: 5px; right: 5px; height: 2px;
            background: rgba(255,255,255,0.7); border-radius: 1px;
        }

        /* ── 내부 본체 ── */
        .fridge-shelves {
            background: #0f172a; border-radius: 4px; padding: 12px; height: 100%; display: flex; gap: 12px;
            box-shadow: inset 0 0 50px rgba(56, 189, 248, 0.1); 
        }
        .shelf-side {
            flex: 1; display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden; padding-right: 4px; position: relative;
        }
        .shelf-side::-webkit-scrollbar, .door-grid-wrapper::-webkit-scrollbar { display: none; }
        .shelf-side { -ms-overflow-style: none; scrollbar-width: none; }

        .shelf-header {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 2px solid rgba(56, 189, 248, 0.3); padding-bottom: 8px; margin-bottom: 15px;
            position: sticky; top: 0; background: #0f172a; z-index: 5; height: 40px; box-shadow: 0 5px 10px rgba(15,23,42,0.8);
        }
        .shelf-title { color: rgba(255,255,255,0.9); font-size: 0.9rem; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 5px; }

        .ai-recommendation-bar { font-size: 0.8rem; font-weight: 600; color: #38bdf8; display: flex; align-items: center; gap: 5px; }
        .ai-recommendation-bar span.ing-item { background: rgba(56,189,248,0.15); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(56,189,248,0.3); color: white;}

        /* 불투명 실사 냉장고 칸막이 느낌 적용 */
        .center-grid { 
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px 8px; align-content: start; 
            /* 하얀/회색 불투명 선반 선 추가 */
            background-image: linear-gradient(to bottom, transparent 92%, #e2e8f0 92%, #94a3b8 100%);
            background-size: 100% 33.33%; padding-bottom: 20px;
        }
        
        .door-grid-wrapper { width: 100%; flex: 1; overflow-y: auto; padding-right: 4px; padding-bottom: 10px; -ms-overflow-style: none; scrollbar-width: none; }
        .door-grid { 
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px 12px; align-content: start; 
            position: relative; padding-bottom: 5px; 
            background-image: linear-gradient(to bottom, transparent 92%, #f8fafc 92%, #cbd5e1 97%, #94a3b8 100%);
            background-size: 100% 33.33%;
        }
        
        /* 문 안쪽 앞부분 덮개(불투명 플라스틱 가드) */
        .door-grid::after {
            content: ''; position: absolute; top: 0; left: -5px; right: -5px; bottom: 0; pointer-events: none; z-index: 10;
            background-image: linear-gradient(to bottom, 
                transparent 78%, 
                rgba(241, 245, 249, 0.9) 78%, 
                rgba(226, 232, 240, 1) 96%, 
                rgba(148, 163, 184, 0.6) 100%
            );
            background-size: 100% 33.33%;
        }

        .ingredient-card { border-radius: 8px; padding: 6px 4px; text-align: center; cursor: pointer; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease; position: relative; }
        .shelf-side .ingredient-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .shelf-side .ingredient-card:hover { background: rgba(255,255,255,0.12); transform: translateY(-4px); box-shadow: 0 6px 12px rgba(0,0,0,0.5); z-index: 11; }
        
        .door-back .ingredient-card {
            background: white; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.06);
            margin: 0 auto; width: 100%; max-width: 130px; z-index: 2;
            transform: translateY(18px); /* 평소에는 바구니에 담겨 밑(금액)이 가려짐 */
        }
        .door-back .ingredient-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.15); z-index: 11; }
        
        .door-back .ingredient-name { color: #1e293b; }
        .ingredient-card.selected { background: rgba(59,130,246,0.2)!important; border-color: #3b82f6!important; box-shadow: 0 0 0 1px #3b82f6 inset!important; }

        .ingredient-img { width: 40px; height: 40px; border-radius: 8px; object-fit: cover; margin: 0 auto 4px; display: block; background: #f1f5f9; }
        .ingredient-img-placeholder { width: 40px; height: 40px; border-radius: 8px; margin: 0 auto 4px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); font-size: 1.2rem; }
        .door-back .ingredient-img-placeholder { background: #f1f5f9; }

        .ingredient-name { font-weight: 700; font-size: 0.75rem; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .ingredient-price { font-size: 0.65rem; color: #94a3b8; text-decoration: line-through; display: block; }
        .ingredient-discount { font-size: 0.75rem; color: #ef4444; font-weight: 800; display: block; margin-top: 1px; }

        .form-area {
            background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; flex: 1; display: flex; flex-direction: column;
            border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .selected-tags {
            flex: 1; min-height: 50px; overflow-y: auto; padding: 8px; background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1;
            display: flex; flex-wrap: wrap; gap: 5px; align-items: flex-start; align-content: flex-start;
        }
        .tag-item { background: #3b82f6; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8rem; display: flex; align-items: center; gap: 4px; }
        .tag-item .remove-tag { cursor: pointer; opacity: 0.8; font-weight: bold; }
        .tag-item .remove-tag:hover { opacity: 1; }
        .form-label { font-size: 0.95rem; }
        .form-select { font-size: 0.85rem; padding: 6px 25px 6px 10px; }

        /* 버튼 둥근 정도 감소 (6px) 및 장보기 버튼 스타일 조정 */
        .btn-action { border-radius: 6px!important; font-size: 0.85rem; font-weight: 600; transition: all 0.2s ease; }
        .btn-crawl {
            background: #fff; color: #10b981; border: 1px solid #10b981; padding: 5px 15px;
        }
        .btn-crawl:hover { background: #ecfdf5; }
        
        .recommend-footer { background: #0f172a; border-top: 1px solid #1e293b; padding: 20px 0; margin-top: 30px; }
        
        .market-title { font-size: 1.1rem; font-weight: 800; text-align: center; margin-bottom: 12px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark sticky-top" id="mainNavbar">
    <div class="container">
        <a class="navbar-brand d-flex align-items-center gap-2" th:href="@{/}">
            <span class="brand-icon">🍽️</span><span class="brand-text">냉장고 레시피</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarContent">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item"><a class="nav-link" th:href="@{/}"><i class="bi bi-house-door me-1"></i>홈</a></li>
                <li class="nav-item" sec:authorize="isAuthenticated()">
                    <a class="nav-link active" th:href="@{/recipe/recommend}"><i class="bi bi-stars me-1"></i>레시피 추천</a>
                </li>
            </ul>
            <div class="d-flex align-items-center gap-3" sec:authorize="isAuthenticated()">
                <span class="text-white-50"><i class="bi bi-person-circle me-1"></i><span sec:authentication="principal.nickname">사용자</span>님</span>
                <a th:href="@{/auth/logout}" class="btn btn-outline-light btn-sm px-3"><i class="bi bi-box-arrow-right me-1"></i>로그아웃</a>
            </div>
            <div class="d-flex align-items-center gap-3" sec:authorize="!isAuthenticated()">
                <a th:href="@{/auth/login}" class="btn btn-outline-light btn-sm px-3"><i class="bi bi-box-arrow-in-right me-1"></i>로그인</a>
            </div>
        </div>
    </div>
</nav>

<main class="py-4">
    <div class="container position-relative">
        <div class="text-center mb-5 mt-2">
            <span class="badge-brand mb-2 d-inline-block">AI 셰프의 주방</span>
            <h2 class="section-title text-white fs-4">오늘의 냉장고를 열어보세요!</h2>
            <p class="section-subtitle text-white-50 small mb-0">문이 활짝 열면 18개의 마트별 추천 식재료를 확인할 수 있습니다.</p>
        </div>

        <div class="fridge-container">
            <div class="fridge-wrapper" id="fridgeWrapper">

                <!-- 내부 본체 (이마트) -->
                <div class="fridge-shelves">
                    <div class="shelf-side">
                        <div class="shelf-header">
                            <h4 class="shelf-title" style="color: #ffb71b;"><i class="bi bi-shop"></i> 이마트</h4>
                            <div class="ai-recommendation-bar" th:if="${recommendedIngredients != null and !recommendedIngredients.isEmpty()}">
                                💡 AI 추천 재료:&nbsp;
                                <span class="ing-item" th:each="ing : ${recommendedIngredients}" th:text="${ing}"></span>
                            </div>
                        </div>
                        <div class="center-grid">
                            <div th:each="item : ${otherItems}" class="ingredient-card"
                                 th:onclick="toggleIngredient(this, [[${item.toIngredientString()}]])">
                                <img th:if="${item.imageUrl != null and !item.imageUrl.isEmpty()}" th:src="${item.imageUrl}" class="ingredient-img" alt="">
                                <div th:if="${item.imageUrl == null or item.imageUrl.isEmpty()}" class="ingredient-img-placeholder">🛒</div>
                                <div class="ingredient-name" th:text="${item.toIngredientString()}">식재료</div>
                                <span class="ingredient-price" th:if="${item.originalPrice != null}" th:text="|${#numbers.formatInteger(item.originalPrice, 0, 'COMMA')}원|"></span>
                                <div class="d-flex justify-content-center align-items-center gap-1 mt-1">
                                    <span class="ingredient-discount" th:text="|${#numbers.formatInteger(item.discountPrice, 0, 'COMMA')}원|"></span>
                                    <span class="discount-rate text-danger fw-bold" style="font-size: 0.7rem;" th:if="${item.originalPrice != null and item.originalPrice > item.discountPrice}" th:text="|${#numbers.formatInteger((item.originalPrice - item.discountPrice) * 100.0 / item.originalPrice, 0)}%↓|"></span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="shelf-side" style="max-width: 320px;">
                        <div class="shelf-header">
                            <h4 class="shelf-title"><i class="bi bi-magic text-warning"></i> 레시피 의뢰</h4>
                        </div>
                        <div class="form-area">
                            <form th:action="@{/recipe/recommend}" method="post" id="recipeForm" class="d-flex flex-column h-100">
                                <input type="hidden" th:name="${_csrf.parameterName}" th:value="${_csrf.token}">
                                <input type="hidden" id="selectedIngredientsInput" name="ingredients" required>
                                <label class="form-label fw-bold text-dark mb-2">선택한 재료 <span class="text-danger">*</span></label>
                                <div class="selected-tags mb-3" id="selectedIngredientsDisplay">
                                    <span class="text-muted small ms-1">재료 카드를 클릭하세요.</span>
                                </div>
                                <label for="healthType" class="form-label fw-bold text-dark mb-2">건강 목표</label>
                                <select class="form-select mb-3" id="healthType" name="health_type">
                                    <option value="일반">일반식 (제한 없음)</option>
                                    <option value="다이어트">다이어트 (저칼로리)</option>
                                    <option value="당뇨">당뇨식 (저당)</option>
                                    <option value="저염식">저염식 (나트륨 최소화)</option>
                                    <option value="벌크업">벌크업 (고단백)</option>
                                </select>
                                <div class="d-flex justify-content-end align-items-center mt-auto gap-2">
                                    <button type="button" class="btn btn-outline-secondary btn-action px-3" onclick="resetSelection()">초기화</button>
                                    <button type="button" class="btn btn-crawl btn-action" id="crawlBtn" onclick="runCrawler()"><i class="bi bi-cart3"></i> 장보기</button>
                                    <button type="submit" class="btn btn-primary btn-action px-4" id="submitBtn" disabled><i class="bi bi-magic me-1"></i>추천 받기</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- 왼쪽 문 (홈플러스) -->
                <div class="fridge-door left-door" id="leftDoor">
                    <div class="door-inner">
                        <div class="door-open-overlay" onclick="toggleFridge()"></div>
                        <div class="door-front">
                            <div class="fridge-door-handle"></div>
                        </div>
                        <div class="door-back">
                            <div class="market-title" style="color: #e30613;"><i class="bi bi-shop"></i> 홈플러스</div>
                            <div class="door-grid-wrapper">
                                <div class="door-grid">
                                    <div th:each="item : ${frozenItems}" class="ingredient-card"
                                         th:onclick="toggleIngredient(this, [[${item.toIngredientString()}]])">
                                        <img th:if="${item.imageUrl != null and !item.imageUrl.isEmpty()}" th:src="${item.imageUrl}" class="ingredient-img" alt="">
                                        <div th:if="${item.imageUrl == null or item.imageUrl.isEmpty()}" class="ingredient-img-placeholder">🥩</div>
                                        <div class="ingredient-name" th:text="${item.toIngredientString()}">식재료</div>
                                        <span class="ingredient-price" th:if="${item.originalPrice != null}" th:text="|${#numbers.formatInteger(item.originalPrice, 0, 'COMMA')}원|"></span>
                                        <div class="d-flex justify-content-center align-items-center gap-1 mt-1">
                                            <span class="ingredient-discount" th:text="|${#numbers.formatInteger(item.discountPrice, 0, 'COMMA')}원|"></span>
                                            <span class="discount-rate text-danger fw-bold" style="font-size: 0.7rem;" th:if="${item.originalPrice != null and item.originalPrice > item.discountPrice}" th:text="|${#numbers.formatInteger((item.originalPrice - item.discountPrice) * 100.0 / item.originalPrice, 0)}%↓|"></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="door-guard-shelf" onclick="toggleFridge()"></div>
                        </div>
                    </div>
                </div>

                <!-- 오른쪽 문 (롯데마트) -->
                <div class="fridge-door right-door" id="rightDoor">
                    <div class="door-inner">
                        <div class="door-open-overlay" onclick="toggleFridge()"></div>
                        <div class="door-front">
                            <div class="home-bar"></div>
                            <div class="fridge-door-handle"></div>
                        </div>
                        <div class="door-back">
                            <div class="market-title" style="color: #ed1c24;"><i class="bi bi-shop"></i> 롯데마트</div>
                            <div class="door-grid-wrapper">
                                <div class="door-grid">
                                    <div th:each="item : ${freshItems}" class="ingredient-card"
                                         th:onclick="toggleIngredient(this, [[${item.toIngredientString()}]])">
                                        <img th:if="${item.imageUrl != null and !item.imageUrl.isEmpty()}" th:src="${item.imageUrl}" class="ingredient-img" alt="">
                                        <div th:if="${item.imageUrl == null or item.imageUrl.isEmpty()}" class="ingredient-img-placeholder">🥬</div>
                                        <div class="ingredient-name" th:text="${item.toIngredientString()}">식재료</div>
                                        <span class="ingredient-price" th:if="${item.originalPrice != null}" th:text="|${#numbers.formatInteger(item.originalPrice, 0, 'COMMA')}원|"></span>
                                        <div class="d-flex justify-content-center align-items-center gap-1 mt-1">
                                            <span class="ingredient-discount" th:text="|${#numbers.formatInteger(item.discountPrice, 0, 'COMMA')}원|"></span>
                                            <span class="discount-rate text-danger fw-bold" style="font-size: 0.7rem;" th:if="${item.originalPrice != null and item.originalPrice > item.discountPrice}" th:text="|${#numbers.formatInteger((item.originalPrice - item.discountPrice) * 100.0 / item.originalPrice, 0)}%↓|"></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="door-guard-shelf" onclick="toggleFridge()"></div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</main>

<footer class="recommend-footer">
    <div class="container text-center">
        <p class="mb-1 text-white-50">
            <span class="fw-semibold" style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">냉장고 레시피</span>
            &nbsp;—&nbsp; AI가 추천하는 오늘의 레시피
        </p>
        <p class="mb-0 text-white-50 small">&copy; 2026 RecipeKR. Built with Spring Boot 3 &amp; Python AI</p>
    </div>
</footer>

<div th:replace="~{fragments/chatbot :: chatbot}"></div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
    const leftDoor = document.getElementById('leftDoor');
    const rightDoor = document.getElementById('rightDoor');
    let isOpen = false;

    // 열기 및 닫기 토글
    function toggleFridge() {
        if (!isOpen) {
            leftDoor.classList.add('open');
            rightDoor.classList.add('open');
            isOpen = true;
        } else {
            leftDoor.classList.remove('open');
            rightDoor.classList.remove('open');
            isOpen = false;
        }
    }

    // URL 파라미터로 열린 상태 진입
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('open') === 'true') {
        leftDoor.querySelector('.door-inner').style.transition = 'none';
        rightDoor.querySelector('.door-inner').style.transition = 'none';
        leftDoor.classList.add('open');
        rightDoor.classList.add('open');
        isOpen = true;
        setTimeout(() => {
            leftDoor.querySelector('.door-inner').style.transition = '';
            rightDoor.querySelector('.door-inner').style.transition = '';
        }, 50);
    }

    // 추천 받기 폼 제출 이벤트 애니메이션
    document.getElementById('recipeForm').addEventListener('submit', function() {
        const btn = document.getElementById('submitBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>레시피 생성 중...';
    });

    function runCrawler() {
        const btn = document.getElementById('crawlBtn');
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>장보는 중...';
        btn.classList.add('disabled');
        fetch('/api/crawler/run', {
            method: 'POST',
            headers: { 'X-CSRF-TOKEN': document.querySelector('input[name="_csrf"]').value }
        }).then(r => r.json()).then(d => {
            window.location.href = '/recipe/recommend?open=true';
        }).catch(err => {
            window.location.href = '/recipe/recommend?open=true';
        });
    }

    const selectedIngredients = new Set();
    const inputEl = document.getElementById('selectedIngredientsInput');
    const displayEl = document.getElementById('selectedIngredientsDisplay');
    const submitBtn = document.getElementById('submitBtn');

    window.toggleIngredient = function(cardElement, itemName) {
        if(!isOpen) return; // 문이 닫혀있으면 작동안함
        if(selectedIngredients.has(itemName)) { selectedIngredients.delete(itemName); cardElement.classList.remove('selected'); }
        else { selectedIngredients.add(itemName); cardElement.classList.add('selected'); }
        updateDisplay();
    };
    window.removeIngredient = function(itemName) {
        selectedIngredients.delete(itemName);
        document.querySelectorAll('.ingredient-card').forEach(c => {
            if(c.querySelector('.ingredient-name').textContent === itemName) c.classList.remove('selected');
        });
        updateDisplay();
    };
    window.resetSelection = function() {
        selectedIngredients.clear();
        document.querySelectorAll('.ingredient-card.selected').forEach(c => c.classList.remove('selected'));
        updateDisplay();
    };
    function updateDisplay() {
        const arr = Array.from(selectedIngredients);
        inputEl.value = arr.join(', ');
        if(!arr.length) {
            displayEl.innerHTML = '<span class="text-muted small ms-1">재료 카드를 클릭하세요.</span>';
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-magic me-1"></i>추천 받기'; // 리셋 시 버튼 텍스트 원상복구
        } else {
            displayEl.innerHTML = arr.map(n => `<span class="tag-item">${n}<span class="remove-tag" onclick="removeIngredient('${n}')">&times;</span></span>`).join('');
            submitBtn.disabled = false;
        }
    }
</script>
</body>
</html>
"""

with open(r"D:\git\202605\recipekr\src\main\resources\templates\recipe\recommend.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("recommend.html rewritten successfully.")
