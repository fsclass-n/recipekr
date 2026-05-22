#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
냉장고 파먹기 - 이마트 할인 상품 크롤러
========================================
대상: 이마트 행사/할인 상품 페이지
방식: Playwright (Chromium headless)
저장: MySQL market_discount 테이블 UPSERT
"""

import asyncio
import logging
import re
from datetime import date
from typing import Optional

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 이마트 식재료 키워드 정규화 매핑
# 상품명에서 핵심 식재료 키워드를 추출하는 용도
# ──────────────────────────────────────────────
INGREDIENT_KEYWORDS = [
    "삼겹살", "목살", "소고기", "닭고기", "돼지고기", "오리", "양고기",
    "연어", "고등어", "갈치", "오징어", "새우", "꽃게", "조개", "전복",
    "두부", "계란", "달걀", "우유", "치즈",
    "양파", "감자", "당근", "마늘", "파", "대파", "생강", "고추",
    "배추", "무", "브로콜리", "시금치", "깻잎", "상추", "양배추",
    "사과", "배", "딸기", "포도", "바나나", "오렌지", "귤", "수박", "참외",
    "버섯", "느타리", "표고", "팽이버섯",
    "쌀", "현미", "보리",
    "된장", "간장", "고추장", "참기름", "들기름", "식용유",
    "라면", "파스타", "국수",
]


def normalize_ingredient(product_name: str) -> str:
    """상품명에서 대표 식재료명을 추출. 매칭 안되면 상품명 첫 2어절 반환."""
    name = product_name.strip()
    for keyword in INGREDIENT_KEYWORDS:
        if keyword in name:
            return keyword
    # 키워드 미매칭 시 첫 2어절 추출
    parts = name.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name


def parse_price(text: Optional[str]) -> Optional[int]:
    """'12,900원' → 12900 정수 변환. 실패 시 None."""
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


async def crawl_emart(page: Page) -> list[dict]:
    """
    이마트 특가/할인 상품 크롤링
    URL: https://emart.ssg.com/sale/salePlanList.ssg
    """
    results = []
    today = date.today().isoformat()

    try:
        logger.info("[이마트] 크롤링 시작...")
        await page.goto(
            "https://emart.ssg.com/sale/salePlanList.ssg",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        await page.wait_for_timeout(2000)

        # 팝업 닫기 시도
        try:
            popup_close = page.locator(".btn_close, .close, [class*='close']").first
            if await popup_close.is_visible(timeout=2000):
                await popup_close.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass

        # 상품 카드 목록 수집
        items = await page.locator(".cunit_thmb, .item_thmb, .unit_thmb").all()

        if not items:
            # 대체 셀렉터 시도
            items = await page.locator("li[class*='item'], .s-card, [class*='goods_item']").all()

        logger.info("[이마트] 발견된 상품 수: %d", len(items))

        for item in items[:50]:  # 최대 50개
            try:
                # 상품명
                name_el = item.locator(".title, .name, [class*='title'], [class*='name']").first
                product_name = (await name_el.inner_text()).strip() if await name_el.count() > 0 else ""

                if not product_name:
                    continue

                # 가격 정보
                sale_price_el = item.locator("[class*='sale'], [class*='discount'], .price").first
                original_price_el = item.locator("[class*='origin'], [class*='before'], s").first

                sale_price_text = await sale_price_el.inner_text() if await sale_price_el.count() > 0 else None
                original_price_text = await original_price_el.inner_text() if await original_price_el.count() > 0 else None

                discount_price = parse_price(sale_price_text)
                original_price = parse_price(original_price_text)

                # 할인율 계산
                discount_rate = None
                if original_price and discount_price and original_price > 0:
                    discount_rate = round((original_price - discount_price) / original_price * 100, 2)

                # 이미지
                img_el = item.locator("img").first
                image_url = await img_el.get_attribute("src") if await img_el.count() > 0 else None
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url

                # 링크
                link_el = item.locator("a").first
                href = await link_el.get_attribute("href") if await link_el.count() > 0 else None
                product_url = href if href and href.startswith("http") else (
                    "https://emart.ssg.com" + href if href else None
                )

                results.append({
                    "market_name": "EMART",
                    "product_name": product_name,
                    "ingredient_name": normalize_ingredient(product_name),
                    "original_price": original_price,
                    "discount_price": discount_price,
                    "discount_rate": discount_rate,
                    "discount_period": None,
                    "image_url": image_url,
                    "product_url": product_url,
                    "crawled_date": today,
                })

            except Exception as e:
                logger.debug("[이마트] 개별 상품 파싱 실패: %s", e)
                continue

        logger.info("[이마트] 크롤링 완료: %d건", len(results))

    except PlaywrightTimeoutError:
        logger.error("[이마트] 페이지 로드 타임아웃")
    except Exception as e:
        logger.error("[이마트] 크롤링 오류: %s", e)

    return results
