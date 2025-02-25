import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv  # 환경 변수 로드용 라이브러리

# .env 파일 로드 (로컬 개발 시 사용, Render에서는 환경 변수 직접 설정)
load_dotenv()

app = Flask(__name__)

# 환경 변수에서 API 키 불러오기
NAVER_API_URL = "https://api.naver.com/keywordstool"
NAVER_API_KEY = os.getenv("NAVER_API_KEY")  # .env 또는 Render 환경 변수에서 가져오기
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # .env 또는 Render 환경 변수에서 가져오기

# Slack API 클라이언트 초기화
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# 네이버 API 호출 함수
def get_related_keywords(keyword):
    headers = {
        "X-API-KEY": NAVER_API_KEY,
        "Content-Type": "application/json"
    }
    params = {
        "hintKeywords": keyword,
        "showDetail": "1"
    }
    response = requests.get(NAVER_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("keywordList", [])
    return None

# Slack Slash Command 핸들러
@app.route("/slack/keywords", methods=["POST"])
def slack_keywords():
    keyword = request.form.get("text")
    channel_id = request.form.get("channel_id")

    if not keyword:
        return jsonify({"text": "검색할 키워드를 입력해주세요!"}), 200

    keywords = get_related_keywords(keyword)
    
    response_text = f"🔎 *'{keyword}' 관련 키워드 목록:*\n"
    if keywords:
        for item in keywords[:10]:
            response_text += f"• {item['relKeyword']} (검색량: {item['monthlyPcQcCnt']})\n"
    else:
        response_text = f"'{keyword}'에 대한 관련 키워드를 찾을 수 없습니다."

    try:
        slack_client.chat_postMessage(channel=channel_id, text=response_text)
    except SlackApiError as e:
        print(f"Slack API Error: {e.response['error']}")

    return jsonify({"response_type": "in_channel", "text": "키워드 검색 중..."}), 200

# Flask 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
