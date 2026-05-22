#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
냉장고 파먹기 - 메인 RPA 크롤러 실행 스크립트
==============================================
이마트, 롯데마트, 홈플러스 3사 할인 식재료를 순차 크롤링하여
MySQL(TiDB) market_discount 테이블에 UPSERT 저장합니다.

사용법:
  # 전체 3사 크롤링 (기본)
  python run_crawler.py

  # 특정 마트만 크롤링
  python run_crawler.py --market emart
  python run_crawler.py --market lottemart
  python run_crawler.py --market homeplus

  # DB 저장 없이 콘솔 출력만 (테스트용)
  python run_crawler.py --dry-run

  # Spring Boot에서 오늘의 할인 재료 조회용 JSON 출력
  python run_crawler.py --output-json
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date

import mysql.connector
from playwright.async_api import async_playwright

from emart_crawler import crawl_emart
from lottemart_crawler import crawl_lottemart
from homeplus_crawler import crawl_homeplus

# ─────────────────────────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # stderr: 로그 (Spring이 JSON과 혼용 방지)
    ],
)
logger = logging.getLogger("run_crawler")


# ─────────────────────────────────────────────────────────────
# DB 연결 설정 (환경 변수 우선, 없으면 기본값 사용)
# ─────────────────────────────────────────────────────────────
def get_db_config() -> dict:
    """환경변수에서 DB 접속 정보를 읽어 반환합니다."""
    tidb_url = os.environ.get("TIDB_URL", "")

    # TIDB_URL에서 호스트/포트/DB명 파싱 (jdbc:mysql://host:port/db?...)
    host = "localhost"
    port = 4000
    database = "recipekr"
    if tidb_url:
        import re
        m = re.search(r"mysql://([^:/]+):?(\d+)?/([^?]+)", tidb_url)
        if m:
            host = m.group(1)
            port = int(m.group(2)) if m.group(2) else 3306
            database = m.group(3)

    return {
        "host": host,
        "port": port,
        "database": database,
        "user": os.environ.get("TIDB_USERNAME", "root"),
        "password": os.environ.get("TIDB_PASSWORD", ""),
        "ssl_disabled": False,
        "charset": "utf8mb4",
        "use_pure": True,
        "connection_timeout": 15,
    }


# ─────────────────────────────────────────────────────────────
# DB UPSERT 저장
# ─────────────────────────────────────────────────────────────
UPSERT_SQL = """
INSERT INTO market_discount (
    market_name, product_name, ingredient_name,
    original_price, discount_price, discount_rate,
    discount_period, image_url, product_url, crawled_date
) VALUES (
    %(market_name)s, %(product_name)s, %(ingredient_name)s,
    %(original_price)s, %(discount_price)s, %(discount_rate)s,
    %(discount_period)s, %(image_url)s, %(product_url)s, %(crawled_date)s
)
ON DUPLICATE KEY UPDATE
    ingredient_name  = VALUES(ingredient_name),
    original_price   = VALUES(original_price),
    discount_price   = VALUES(discount_price),
    discount_rate    = VALUES(discount_rate),
    discount_period  = VALUES(discount_period),
    image_url        = VALUES(image_url),
    product_url      = VALUES(product_url),
    updated_at       = NOW()
"""


def save_to_db(items: list[dict]) -> int:
    """크롤링 결과를 DB에 UPSERT 저장. 저장 건수 반환."""
    if not items:
        return 0

    config = get_db_config()
    saved = 0

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        for item in items:
            try:
                cursor.execute(UPSERT_SQL, item)
                saved += 1
            except mysql.connector.Error as e:
                logger.warning("DB 저장 실패 [%s]: %s", item.get("product_name"), e)

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("DB 저장 완료: %d건", saved)

    except mysql.connector.Error as e:
        logger.error("DB 연결 실패: %s", e)

    return saved


# ─────────────────────────────────────────────────────────────
# 오늘의 할인 재료 조회 (Spring Boot predict.py 연동용)
# ─────────────────────────────────────────────────────────────
def get_today_discount_ingredients() -> list[dict]:
    """오늘 날짜 기준 DB에서 할인 식재료 목록을 조회하여 반환합니다."""
    config = get_db_config()
    today = date.today().isoformat()

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT market_name, product_name, ingredient_name,
                   discount_price, discount_rate, discount_period, image_url
            FROM market_discount
            WHERE crawled_date = %s
            ORDER BY market_name, discount_rate DESC
            """,
            (today,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except mysql.connector.Error as e:
        logger.error("할인 재료 조회 실패: %s", e)
        return []


# ─────────────────────────────────────────────────────────────
# 메인 실행 로직
# ─────────────────────────────────────────────────────────────
async def run_crawlers(market: str = "all", dry_run: bool = False) -> list[dict]:
    """
    지정된 마트의 할인 상품을 크롤링합니다.

    :param market: 'all' | 'emart' | 'lottemart' | 'homeplus'
    :param dry_run: True이면 DB 저장 없이 콘솔만 출력
    :return: 전체 수집된 상품 리스트
    """
    all_results = []

    async with async_playwright() as pw:
        # Headless Chromium 브라우저 실행
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--lang=ko-KR",
            ],
        )

        # 브라우저 컨텍스트 (언어 및 뷰포트 설정)
        context = await browser.new_context(
            locale="ko-KR",
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        # ── 이마트 ─────────────────────────────────────────
        if market in ("all", "emart"):
            try:
                emart_results = await crawl_emart(page)
                all_results.extend(emart_results)
                if not dry_run:
                    save_to_db(emart_results)
            except Exception as e:
                logger.error("[이마트] 실행 오류: %s", e)

        # ── 롯데마트 ───────────────────────────────────────
        if market in ("all", "lottemart"):
            try:
                lotte_results = await crawl_lottemart(page)
                all_results.extend(lotte_results)
                if not dry_run:
                    save_to_db(lotte_results)
            except Exception as e:
                logger.error("[롯데마트] 실행 오류: %s", e)

        # ── 홈플러스 ───────────────────────────────────────
        if market in ("all", "homeplus"):
            try:
                homeplus_results = await crawl_homeplus(page)
                all_results.extend(homeplus_results)
                if not dry_run:
                    save_to_db(homeplus_results)
            except Exception as e:
                logger.error("[홈플러스] 실행 오류: %s", e)

        await browser.close()

    logger.info("=== 전체 크롤링 완료: 총 %d건 수집 ===", len(all_results))
    return all_results


def main():
    parser = argparse.ArgumentParser(description="대형마트 할인 식재료 RPA 크롤러")
    parser.add_argument(
        "--market",
        choices=["all", "emart", "lottemart", "homeplus"],
        default="all",
        help="크롤링할 마트 선택 (기본: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="DB 저장 없이 콘솔 출력만 수행 (테스트용)",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="오늘의 할인 재료를 DB에서 조회하여 JSON 출력 (Spring Boot 연동용)",
    )
    args = parser.parse_args()

    # Spring Boot가 오늘의 할인 재료를 직접 조회하는 모드
    if args.output_json:
        discount_list = get_today_discount_ingredients()
        # stdout에 JSON 출력 (Spring Boot ProcessBuilder가 읽어감)
        print(json.dumps(discount_list, ensure_ascii=False, default=str))
        return

    # 크롤링 실행
    results = asyncio.run(run_crawlers(market=args.market, dry_run=args.dry_run))

    if args.dry_run:
        # dry-run: 수집 결과를 JSON으로 콘솔 출력
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        logger.info("크롤링 및 DB 저장 완료 (총 %d건)", len(results))


if __name__ == "__main__":
    main()
