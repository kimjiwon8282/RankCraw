import json
import os
import logging

logger = logging.getLogger(__name__)


def load_categories(file_name: str, folder: str = 'category_data') -> list:
    """
    폴더 내 JSON 파일을 읽어 카테고리 리스트를 반환합니다.
    """
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, folder, file_name)
    if not os.path.exists(path):
        logger.error("Category file not found: %s", path)
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_queries(categories: list) -> list:
    """
    각 카테고리 맵에서 가장 디테일한 분류(세분류>소분류>중분류)를 가져오고,
    '/' 로 구분된 경우 각각 분리해서 반환합니다.
    """
    queries = []
    for cat in categories:
        # 세분류, 소분류, 중분류 순서로 우선값 선택
        combined = cat.get('세분류') or cat.get('소분류') or cat.get('중분류')
        if not combined:
            continue
        # '/' 구분자 분리
        for kw in combined.split('/'):
            kw = kw.strip()
            if kw:
                queries.append(kw)
    return queries
