import time 
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager
from db_utils import insert_documents

# ─── 로거 설정 ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def crawl(query: str = "쌈채소"):
    logger.info("크롤링 시작: query=%s", query)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(1)
    driver.get(f"https://search.shopping.naver.com/ns/search?query={query}")

    saved_count = 0
    scroll_count = 0
    MAX_SCROLL = 4
    docs = []
    prev_count = 0

    # 동적 스크롤: 최대 MAX_SCROLL회, 저장된 아이템 50개 될 때까지
    while saved_count < 50 and scroll_count < MAX_SCROLL:
        scroll_count += 1
        logger.info("스크롤 %d/%d", scroll_count, MAX_SCROLL)
        # 첫 스크롤은 viewport 높이만큼, 이후에는 5배 스크롤
        if scroll_count == 1:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
        else:
            driver.execute_script("window.scrollBy(0, window.innerHeight * 5);")
        time.sleep(1)

        items = driver.find_elements(By.CSS_SELECTOR, "li.composite_card_container")
        total_items = len(items)
        logger.info("로드된 총 요소: %d", total_items)

        # 새 상품이 없으면 종료
        if total_items == prev_count:
            logger.info("새로운 아이템이 없습니다. 크롤링 종료.")
            break

        # 이전에 처리한 부분 이후부터 순회
        for item in items[prev_count:]:
            if saved_count >= 50:
                break
            try:
                # 상품명 추출
                try:
                    name = item.find_element(
                        By.CSS_SELECTOR,
                        ".basicProductCard_basic_product_card__TdrHT .productCardTitle_product_card_title__eQupA"
                    ).text.strip()
                except NoSuchElementException:
                    prev_count += 1
                    continue
                if not name:
                    prev_count += 1
                    continue

                # 별점 추출
                try:
                    raw = item.find_element(
                        By.CSS_SELECTOR,
                        ".basicProductCard_basic_product_card__TdrHT .productCardReview_star__7iHNO"
                    ).text.replace("별점", "").strip()
                    rating = float(raw)
                except (NoSuchElementException, ValueError):
                    rating = 0.0

                # 리뷰 수 추출
                try:
                    review_text = item.find_element(
                        By.CSS_SELECTOR,
                        ".basicProductCard_basic_product_card__TdrHT .productCardReview_with_review_text__KreLb span:nth-of-type(2)"
                    ).text
                    digits = ''.join(filter(str.isdigit, review_text))
                    review_count = int(digits) if digits else 0
                except (NoSuchElementException, ValueError):
                    review_count = 0

                saved_count += 1
                rank = saved_count
                logger.info(
                    "저장 %2d → 상품명: %s | 별점: %.2f | 리뷰 수: %d", 
                    saved_count, name, rating, review_count
                )

                # 저장할 문서 누적
                docs.append({
                    "keyword": query,
                    "rank": rank,
                    "name": name,
                    "rating": rating,
                    "review_count": review_count,
                    "crawled_at": datetime.utcnow()
                })
                prev_count += 1

            except StaleElementReferenceException:
                logger.warning("StaleElementReferenceException 발생, 스킵")
                prev_count += 1
                continue

    driver.quit()

    # 수집된 개수에 따른 예외 처리
    if saved_count == 0:
        logger.error("키워드 '%s' 로 수집된 상품이 없습니다.", query)
        return
    elif saved_count < 50:
        logger.warning("키워드 '%s' 로 총 %d개만 수집되었습니다 (목표 50개).", query, saved_count)

    # MongoDB에 일괄 저장
    if docs:
        ids = insert_documents(docs, collection="products", replace_existing_keyword=True)
        logger.info("MongoDB에 저장된 문서 수: %d", len(ids))

    logger.info("크롤링 종료")

if __name__ == "__main__":
    crawl()
