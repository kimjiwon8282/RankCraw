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

# 4) MongoDB URI 조합
URI = (
    f"mongodb+srv://{USER}:{ENCODED_PW}"
    f"@{CLUSTER}/?retryWrites=true"
    "&w=majority"
    "&appName=Ranking"
)

#몽고Client 생성(Server API 버전 1 사용)
_client = MongoClient(URI,server_api = ServerApi("1"))
#지정된 데이터베이스 인스턴스
_db = _client[DBNAME]

def get_db():
    """
    MongoDB 데이터베이스 객체 반환
    """
    return _db

def ping():
    """
    연결 확인용 ping
    """
    try:
        _client.admin.command("ping")
        print("Ping 성공:MongoDB 연결 완료")
    except Exception as e:
        print("ping fail:",e)

# 파일 맨 아래에 추가
if __name__ == "__main__":
    ping()

