import os
import time
import csv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
#  크롬 드라이버 자동 업데이트를 위한 webdriver_manager 사용
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse  # URL 인코딩에 사용
from number_utils import transNumber

# ─── 1) uploads 디렉터리 경로 설정 ─────────────────────────────────────────────
# 이 스크립트가 있는 폴더 기준으로 uploads 폴더를 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# CSV 파일 경로
csv_path = os.path.join(UPLOAD_DIR, 'data2.csv')

# ─── 2) CSV 파일 열기 ─────────────────────────────────────────────────────────
# 인코딩은 윈도우 엑셀 호환을 위해 CP949 사용
with open(csv_path, 'w', encoding='cp949', newline='') as f:
    csvWriter = csv.writer(f)
    csvWriter.writerow(['rank','name','price','rating','rating_count','purchase_count','wish_count','link'])
    
    # ─── 3) Selenium 드라이버 준비 ────────────────────────────────────────────
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    # 검색어 및 URL 인코딩
    query = "쌈채소"
    encoded_query = urllib.parse.quote(query)
    rank = 0
    
    # ─── 4) 크롤링 루프 ────────────────────────────────────────────────────────
    for page in range(1, 6):
        url = (
            f"https://msearch.shopping.naver.com/search/all?"
            f"adQuery={encoded_query}&origQuery={encoded_query}"
            f"&pagingIndex={page}&pagingSize=40&productSet=total"
            f"&query={encoded_query}&sort=rel&viewType=list"
        )
        print(f"[INFO] {page} 페이지 접속: {url}")
        driver.get(url)
        time.sleep(0.3)
        
        # 동적 스크롤
        before_h = driver.execute_script("return window.scrollY")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            after_h = driver.execute_script("return window.scrollY")
            if after_h == before_h:
                break
            before_h = after_h
        
        # 상품 정보 추출
        items = driver.find_elements(By.CSS_SELECTOR, ".product_list_item__blfKk")
        print(f"[INFO] {len(items)} 개의 상품 정보 발견")
        
        for item in items:
            try:
                name = item.find_element(By.CSS_SELECTOR, ".product_info_tit__UOCqq").text
            except:
                name = "이름 없음"
            try:
                price_text = item.find_element(By.CSS_SELECTOR, ".product_num__dWkfq").text
                price = int(price_text.replace(",", "").replace("원", "").strip())
            except:
                price = -1
            try:
                link = item.find_element(
                    By.CSS_SELECTOR,
                    "a.product_btn_link__AhZaM._nlog_click.linkAnchor"
                ).get_attribute("href")
            except:
                link = "링크없음"
            try:
                info_div = item.find_element(
                    By.CSS_SELECTOR,
                    "div.product_info_count__J6ElA"
                )
            except NoSuchElementException:
                # info_div 자체가 없으면 모두 0
                rating = "0.0"
                rating_count = "0"
                purchase_count = "0"
                wish_count = "0"
            else:
            # 2) 평점 & 평점수
                try:
                    rating = info_div.find_element(
                        By.CSS_SELECTOR,
                        "span.product_grade__eU8gY strong"
                    ).text
                    rating_count_temp = info_div.find_element(
                        By.CSS_SELECTOR,
                        "span.product_grade__eU8gY em"
                    ).text.replace(",", "")
                    rating_count = transNumber(rating_count_temp)
                except NoSuchElementException:
                    rating = "0.0"
                    rating_count = "0"

                # 3) 구매수 (텍스트 “구매”이 포함된 span 찾기)
                try:
                    purchase_span = info_div.find_element(
                        By.XPATH,
                        ".//span[contains(normalize-space(), '구매')]"
                    )
                    purchase_count_temp = purchase_span.find_element(
                        By.TAG_NAME, "em"
                    ).text.replace(",", "")
                    purchase_count = transNumber(purchase_count_temp)
                except NoSuchElementException:
                    purchase_count = "0"

                # 4) 찜수 (텍스트 “찜”이 포함된 span 찾기)
                try:
                    wish_span = info_div.find_element(
                        By.XPATH,
                        ".//span[contains(normalize-space(), '찜')]"
                    )
                    wish_count_temp = wish_span.find_element(
                        By.TAG_NAME, "em"
                    ).text.replace(",", "")
                    wish_count = transNumber(wish_count_temp)
                except NoSuchElementException:
                    wish_count = "0"

            rank+=1
            csvWriter.writerow([rank,name,price,rating,rating_count,purchase_count,wish_count,link])

print(f"[DONE] CSV 저장 경로: {csv_path}")
time.sleep(3600)

