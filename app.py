import os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ✅ 환경 변수에서 Slack 토큰 가져오기
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
slack_client = WebClient(token=SLACK_BOT_TOKEN)

app = Flask(__name__)

#  Slack에서 `/search_trend` 호출 시 응답 테스트
@app.route("/slack/search_trend", methods=["POST"])
def slack_search_trend():
    print("[LOG] Slack 요청 수신")  #  로그 출력

    # Slack에서 받은 데이터
    data = request.form
    command_text = data.get("text", "").split()

    if len(command_text) < 4:
        return jsonify({"text": "올바른 형식: /search_trend kwd1 kwd2 days device"}), 200

    # 입력값 확인
    kwd1, kwd2, days, device = command_text[0], command_text[1], command_text[2], command_text[3]
    response_text = f" '{kwd1} {kwd2} {days} {device}' 입력수신완료"

    #  Slack에 메시지 전송
    try:
        slack_client.chat_postMessage(
            channel=data["channel_id"],
            text=response_text
        )
        print("[LOG] Slack 메시지 전송 성공:", response_text)
    except SlackApiError as e:
        print(f"❌ Slack 메시지 전송 실패: {e.response['error']}")

    return jsonify({"text": response_text}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
