import time 
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
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

    # 한 번에 충분히 스크롤하여 상품을 로드
    scroll_distance = driver.execute_script("return window.innerHeight;") * 7
    logger.info("초기 대량 스크롤: %dpx", scroll_distance)
    driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
    time.sleep(1)

    # 상품 요소 수집
    items = driver.find_elements(By.CSS_SELECTOR, "li.composite_card_container")
    total_items = len(items)
    logger.info("로드된 총 요소: %d", total_items)

    saved_count = 0
    docs = []

    # 상위 100개만 처리
    for item in items[:30]:
        try:
            # 광고 상품 건너뛰기:
            # data-shp-contents-grp="ad" OR 광고 아이콘(svg.advertisementTag_icon) OR span.blind 텍스트에 '광고' 포함
            has_ad_attr = bool(item.find_elements(By.CSS_SELECTOR, "[data-shp-contents-grp='ad']"))
            has_ad_svg = bool(item.find_elements(By.CSS_SELECTOR, "svg[class*='advertisementTag_icon']"))
            has_ad_text = any(span.text.strip().find('광고') != -1 for span in item.find_elements(By.CSS_SELECTOR, "span.blind"))
            if has_ad_attr or has_ad_svg or has_ad_text:
                continue

            # 상품명
            try:
                name = item.find_element(
                    By.CSS_SELECTOR,
                    ".basicProductCard_basic_product_card__TdrHT .productCardTitle_product_card_title__eQupA"
                ).text.strip()
            except NoSuchElementException:
                continue
            if not name:
                continue

            # 별점
            try:
                raw = item.find_element(
                    By.CSS_SELECTOR,
                    ".basicProductCard_basic_product_card__TdrHT .productCardReview_star__7iHNO"
                ).text.replace("별점", "").strip()
                rating = float(raw)
            except (NoSuchElementException, ValueError):
                rating = 0.0

            # 리뷰 수
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
                rank, name, rating, review_count
            )

            docs.append({
                "keyword": query,
                "rank": rank,
                "name": name,
                "rating": rating,
                "review_count": review_count,
                "crawled_at": datetime.utcnow()
            })

        except Exception as e:
            logger.warning("처리 중 오류 발생: %s", e)
            continue

    # 크롤링 완료 후 브라우저 유지
    driver.quit()

    # 예외 처리 및 저장
    if saved_count == 0:
        logger.error("키워드 '%s' 로 수집된 상품이 없습니다.", query)
        return
    elif saved_count < 100:
        logger.warning("키워드 '%s' 로 총 %d개만 수집되었습니다 (요청 100개).", query, saved_count)

    if docs:
        ids = insert_documents(docs, collection="products", replace_existing_keyword=True)
        logger.info("MongoDB에 저장된 문서 수: %d", len(ids))

    logger.info("크롤링 종료")

if __name__ == "__main__":
    crawl()
