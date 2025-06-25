import time
import urllib.parse
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from db_utils import insert_documents
from datetime import datetime

def crawl(query: str = "쌈채소", scroll_times: int = 7):
    """
    네이버 쇼핑 통합검색 페이지에서 광고 상품을 제외하고, 주어진 횟수만큼 스크롤 후
    비광고 상품 랭킹과 주요 정보를 수집하여 MongoDB에 저장합니다.
    Args:
      query: 검색어
      scroll_times: 스크롤 반복 횟수
    """
    # ChromeDriver 초기화
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # 검색 페이지 접속
    encoded_query = urllib.parse.quote(query)
    url = f"https://search.shopping.naver.com/ns/search?query={encoded_query}"
    print(f"[INFO] 접속 URL: {url}")
    driver.get(url)

    # 지정 횟수만큼 스크롤
    for i in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0)
        print(f"[INFO] 스크롤 {i+1}/{scroll_times}")

    # 상품 요소 수집
    items = driver.find_elements(By.CSS_SELECTOR, "li.compositeCardContainer_composite_card_container__jr8cb")
    print(f"[INFO] 총 {len(items)}개의 상품 요소 발견")

    docs = []
    non_ad_rank = 0
    for item in items:
        try:
            # 광고 상품 제외
            try:
                item.find_element(By.CSS_SELECTOR, ".advertisementTag_advertisement_tag__yIvim")
                continue
            except NoSuchElementException:
                pass

            non_ad_rank += 1

            # 가게명
            try:
                store = item.find_element(By.CSS_SELECTOR, ".productCardMallLink_mall_name__5oWPw").text
            except NoSuchElementException:
                store = ""

            # 상품명
            try:
                name = item.find_element(By.CSS_SELECTOR, ".productCardTitle_product_card_title__eQupA").text
            except NoSuchElementException:
                name = ""

            # 가격
            try:
                price_text = item.find_element(By.CSS_SELECTOR, ".priceTag_number__1QW0R").text
                price = int(price_text.replace(",", "").strip())
            except:
                price = 0

            # 평점
            try:
                rating_text = item.find_element(By.CSS_SELECTOR, ".productCardReview_star__7iHNO").text
                rating = float(rating_text)
            except:
                rating = 0.0

            # 리뷰 수
            try:
                review_text = item.find_element(
                    By.CSS_SELECTOR,
                    "div.productCardReview_with_review_text__KreLb > span:nth-of-type(2)"
                ).text
                review = int(''.join(filter(str.isdigit, review_text)))
            except:
                review = 0

            docs.append({
                "keyword": query,
                "ranking": non_ad_rank,
                "store": store,
                "name": name,
                "price": price,
                "rating": rating,
                "review_count": review,
                "crawled_at": datetime.utcnow()
            })
        except StaleElementReferenceException:
            print("[WARN] StaleElementReferenceException 발생, 항목 스킵")
            continue

    # 브라우저 종료
    input("크롤링 완료. 브라우저를 닫으려면 엔터를 누르세요...")
    driver.quit()

    # MongoDB 저장
    if docs:
        ids = insert_documents(docs, collection="products")
        print(f"[DB] 저장된 문서 수: {len(ids)}")

    print("[DONE] 크롤링 완료")
