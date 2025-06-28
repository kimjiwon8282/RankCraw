import logging
from category_utils import load_categories, extract_queries
from crawling import crawl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def main():
    # Vegetable 카테고리 JSON 로드
    cats = load_categories('categoryDataVegetable.json')
    queries = extract_queries(cats)

    logger.info("총 %d개의 키워드 준비 완료", len(queries))
    for idx, q in enumerate(queries, start=1):
        logger.info("[%d/%d] 크롤링 시작: '%s'", idx, len(queries), q)
        try:
            crawl(q)
        except Exception as e:
            logger.error("키워드 '%s' 크롤링 중 오류: %s", q, e)

    logger.info("모든 크롤링 작업 완료")

if __name__ == '__main__':
    main()