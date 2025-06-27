import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

USER      = os.getenv("MONGO_USER")
PASSWORD  = os.getenv("MONGO_PASSWORD")
CLUSTER   = os.getenv("MONGO_CLUSTER")
DBNAME    = os.getenv("MONGO_DBNAME", "test")

ENCODED_PW = quote_plus(PASSWORD)

URI = (
    f"mongodb+srv://{USER}:{ENCODED_PW}"
    f"@{CLUSTER}/?retryWrites=true"
    "&w=majority"
    "&appName=Ranking"
)

_client = MongoClient(URI, server_api=ServerApi("1"))
_db = _client[DBNAME]

def get_db():
    return _db

def ping():
    try:
        _client.admin.command("ping")
        print("✅ Ping 성공: MongoDB 연결 완료!")
    except Exception as e:
        print("❌ Ping 실패:", e)
        raise

def insert_documents(
    docs: list,
    collection: str = "products",
    replace_existing_keyword: bool = False
) -> list:
    """
    Args:
      docs: 저장할 문서 리스트
      collection: 컬렉션 이름
      replace_existing_keyword: True 이면, 같은 keyword 문서 먼저 삭제
    Returns:
      삽입된 문서들의 ObjectId 리스트
    """
    if not docs:
        return []

    col = _db[collection]
    if replace_existing_keyword:
        keyword = docs[0].get("keyword")
        if keyword:
            col.delete_many({"keyword": keyword})

    result = col.insert_many(docs)
    return result.inserted_ids

# 모듈 import 시 ping 실행
ping()
