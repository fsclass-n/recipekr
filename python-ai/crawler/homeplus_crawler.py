#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
냉장고 파먹기 - 홈플러스 할인 상품 크롤러
==========================================
대상: 홈플러스 이번주 특가/할인 상품 페이지
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
    name = product_name.strip()
    for keyword in INGREDIENT_KEYWORDS:
        if keyword in name:
            return keyword
    parts = name.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name


def parse_price(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


async def crawl_homeplus(page: Page) -> list[dict]:
    """
    홈플러스 이번주 특가 상품 크롤링
    URL: https://mobileapp.homeplus.co.kr/event
    """
    results = []
    today = date.today().isoformat()

    try:
        logger.info("[홈플러스] 크롤링 시작...")
        await page.goto(
            "https://homeplus.co.kr/Page/EventWeekly",
            wait_until="domcontentloaded",
            timeout=35000,
        )
        await page.wait_for_timeout(2500)

        # 팝업 닫기
        try:
            for selector in [".close", ".btn-close", "[class*='popup-close']", "[aria-label='close']"]:
                els = await page.locator(selector).all()
                for el in els:
                    if await el.is_visible(timeout=1000):
                        await el.click()
                        await page.wait_for_timeout(300)
        except Exception:
            pass

        # 무한 스크롤 또는 더보기 클릭 (최대 2회)
        for _ in range(2):
            try:
                more_btn = page.locator(
                    "button:has-text('더보기'), .btn-more, [class*='load-more']"
                ).first
                if await more_btn.is_visible(timeout=2000):
                    await more_btn.click()
                    await page.wait_for_timeout(1500)
                else:
                    # 페이지 하단 스크롤로 지연 로딩 유발
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)
            except Exception:
                break

        # 상품 카드 수집 (여러 셀렉터 시도)
        items = await page.locator(
            ".product-card, .goods-card, [class*='product-item'], "
            "[class*='goods-item'], .item, li[class*='prd']"
        ).all()

        logger.info("[홈플러스] 발견된 상품 수: %d", len(items))

        for item in items[:50]:
            try:
                # 상품명
                name_el = item.locator(
                    ".product-name, .goods-name, .prd-name, [class*='product-name'], .name"
                ).first
                product_name = (await name_el.inner_text()).strip() if await name_el.count() > 0 else ""

                if not product_name:
                    continue

                # 할인가
                sale_el = item.locator(
                    ".sale-price, .event-price, [class*='sale'], [class*='discount-price'], .price"
                ).first
                # 정가
                origin_el = item.locator(
                    ".original-price, [class*='origin'], s, del, [class*='before-price']"
                ).first
                # 할인 기간
                period_el = item.locator("[class*='period'], [class*='date'], .event-date").first

                sale_text = await sale_el.inner_text() if await sale_el.count() > 0 else None
                origin_text = await origin_el.inner_text() if await origin_el.count() > 0 else None
                period_text = await period_el.inner_text() if await period_el.count() > 0 else None

                discount_price = parse_price(sale_text)
                original_price = parse_price(origin_text)

                discount_rate = None
                if original_price and discount_price and original_price > 0:
                    discount_rate = round((original_price - discount_price) / original_price * 100, 2)

                # 이미지
                img_el = item.locator("img").first
                image_url = await img_el.get_attribute("src") if await img_el.count() > 0 else None
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url

                # 상품 링크
                link_el = item.locator("a").first
                href = await link_el.get_attribute("href") if await link_el.count() > 0 else None
                product_url = href if href and href.startswith("http") else (
                    "https://homeplus.co.kr" + href if href else None
                )

                results.append({
                    "market_name": "HOMEPLUS",
                    "product_name": product_name,
                    "ingredient_name": normalize_ingredient(product_name),
                    "original_price": original_price,
                    "discount_price": discount_price,
                    "discount_rate": discount_rate,
                    "discount_period": period_text,
                    "image_url": image_url,
                    "product_url": product_url,
                    "crawled_date": today,
                })

            except Exception as e:
                logger.debug("[홈플러스] 개별 상품 파싱 실패: %s", e)
                continue

        logger.info("[홈플러스] 크롤링 완료: %d건", len(results))

    except PlaywrightTimeoutError:
        logger.error("[홈플러스] 페이지 로드 타임아웃")
    except Exception as e:
        logger.error("[홈플러스] 크롤링 오류: %s", e)

    return results
