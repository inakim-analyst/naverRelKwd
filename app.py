#연관검색어의 월별검색수 확인
import os
import sys
import urllib.request
import json
import pandas as pd
import matplotlib.pyplot as plt
import time
import random
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv  # 환경 변수 로드용 라이브러리

import hashlib
import hmac
import base64

from flask import Flask, request, jsonify, send_file
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

plt.rc('font', family='NanumGothic') 
# urllib.disable_warnings()

#전역변수
# .env 파일 로드 (로컬 개발 시 사용, Render에서는 환경 변수 직접 설정)
load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # Render 환경 변수에서 가져오기
slack_client = WebClient(token=SLACK_BOT_TOKEN)  # Slack API 클라이언트 초기화

app = Flask(__name__)

class Signature:

    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)

        hash.hexdigest()
        return base64.b64encode(hash.digest())


def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(round(time.time() * 1000))
    signature = Signature.generate(timestamp, method, uri, secret_key)

    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 
            'X-API-KEY': api_key, 'X-Customer': str(customer_id), 'X-Signature': signature}


def getrelkeyword(keyword1,keyword2):

    BASE_URL = 'https://api.naver.com'
    # Render 환경 변수에서 가져오기
    API_KEY =  os.getenv("API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")  
    CUSTOMER_ID = os.getenv("CUSTOMER_ID")  

    uri = '/keywordstool'
    method = 'GET'

    params={}

    params = {
        'hintKeywords': f"{keyword1},{keyword2}",  # 키워드 순서 유지
        'showDetail': '1'
    }
    # params['hintKeywords'] = ','.join([keyword1, keyword2])
    # params['showDetail']='1'

    r=requests.get(BASE_URL + uri, params=params, verify=False,
                 headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))

    return pd.DataFrame(r.json()['keywordList'])

#통합검색어 트렌드 확인

def gettrenddata(keyword1,keyword2,startDate,endDate):
    # .Render 환경 변수에서 가져오기
    CLIENT_ID =  os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")  

    timeUnit='month' ## date, week, month
    keywordGroups=[
        {'groupName':keyword1, 'keywords':[keyword1]},
        {'groupName':keyword2, 'keywords':[keyword2]},
    ]

    url = "https://openapi.naver.com/v1/datalab/search";

    response_results_all = pd.DataFrame()

    body_dict={} #검색 정보를 저장할 변수
    body_dict['startDate']=startDate
    body_dict['endDate']=endDate
    body_dict['timeUnit']=timeUnit
    body_dict['keywordGroups']=keywordGroups
    body_dict['device']="mo"

    body=str(body_dict).replace("'",'"') # ' 문자로는 에러가 발생해서 " 로 변환

    # request = urllib.request.Request(url)
    # request.add_header("X-Naver-Client-Id",CLIENT_ID)
    # request.add_header("X-Naver-Client-Secret",CLIENT_SECRET)
    # request.add_header("Content-Type","application/json")
    # response = urllib.request.urlopen(request, data=body.encode("utf-8"))
    # rescode = response.getcode()
    # if(rescode==200):
    #     response_body = response.read()
    #     response_json = json.loads(response_body)
    # else:
    #     print("Error Code:" + rescode)

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id",CLIENT_ID)
    request.add_header("X-Naver-Client-Secret",CLIENT_SECRET)
    request.add_header("Content-Type","application/json")
    response = urllib.request.urlopen(request, data=body.encode("utf-8"))
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        response_json = json.loads(response_body)
        print(response_body.decode('utf-8'))
    else:
        print("Error Code:" + rescode)

    # 결과데이터중 'data' 와 'title'만 따로 DataFrame으로 저장
    response_results = pd.DataFrame()
    for data in response_json['results']:
        result=pd.DataFrame(data['data'])
        result['title']=data['title']

        response_results = pd.concat([response_results,result])

    return response_results

def calculate_search_trend(keyword1, keyword2, days_ago=30, device="mo"):
    """
    주어진 키워드들에 대한 네이버 데이터랩 검색 트렌드 및 검색량을 계산하는 함수.

    :param keyword1: 첫 번째 키워드 (str)
    :param keyword2: 두 번째 키워드 (str)
    :param device: 검색 대상 (str) - "pc" 또는 "mo" (기본값: "mo")
    :param days_ago: 데이터를 보기 시작할 날짜. (int) (기본값:30)
    :return: 계산된 검색 트렌드 데이터 (DataFrame)
    """
    today_date = datetime.today()

    # 검색 기간 설정 (days_ago일 전 ~ 1일 전)
    startDate = (today_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    endDate = (today_date - timedelta(days=1)).strftime('%Y-%m-%d')

    # 데이터 가져오기
    trend = gettrenddata(keyword1, keyword2, startDate, endDate)
    relkeyword = getrelkeyword(keyword1, keyword2)

    if trend is None or relkeyword is None:
        print("데이터를 가져오지 못했습니다.")
        return None

    # 키워드별 최신 퍼센트 정보 저장
    keyword1_percent = trend.loc[trend['title'] == keyword1, 'ratio'].iloc[-1]
    keyword2_percent = trend.loc[trend['title'] == keyword2, 'ratio'].iloc[-1]

    # 디바이스별 컬럼 선택 (PC: 1, Mobile: 2)
    colnum = 1 if device == 'pc' else 2

    # 키워드별 검색수 저장 (PC/Mobile)
    keyword1_count = relkeyword.loc[relkeyword['relKeyword'] == keyword1].iloc[0, colnum]
    keyword2_count = relkeyword.loc[relkeyword['relKeyword'] == keyword2].iloc[0, colnum]

    # 검색수 / 1% 비율 계산
    keyword1_1percent = keyword1_count / keyword1_percent
    keyword2_1percent = keyword2_count / keyword2_percent

    # 최종 트렌드 데이터에 검색수 계산 추가
    trend_fin = trend.copy()
    trend_fin.loc[trend_fin['title'] == keyword1, (device + '검색수')] = \
        keyword1_1percent * trend_fin.loc[trend_fin['title'] == keyword1, 'ratio']
    trend_fin.loc[trend_fin['title'] == keyword2, (device + '검색수')] = \
        keyword2_1percent * trend_fin.loc[trend_fin['title'] == keyword2, 'ratio']

    # 검색수 데이터 정수형 변환
    trend_fin = trend_fin.astype({(device + '검색수'): 'int64'})
    
    # 컬럼명 변경 (period → month, title → keyword)
    trend_fin = trend_fin.rename(columns={"period": "month", "title": "keyword"})

    return trend_fin


# Slack에서 호출하는 API 엔드포인트
# @app.route("/slack/search_trend", methods=["POST"])
# def slack_search_trend():
#     data = request.form
#     command_text = data.get("text", "").split()
    
#     if len(command_text) < 4:
#         return jsonify({"text": "올바른 형식: /search_trend keyword1 keyword2 days device"}), 200

#     keyword1, keyword2, days, device = command_text[0], command_text[1], int(command_text[2]), command_text[3]

#     result_df = calculate_search_trend(keyword1, keyword2, days_ago=days, device=device)
#     if result_df is None:
#         return jsonify({"text": "데이터를 가져오지 못했습니다."}), 200

#     # CSV 저장
#     csv_filename = "search_trend.csv"
#     result_df.to_csv(csv_filename, index=False)

#     # Slack에 CSV 파일 업로드
#     try:
#         response = slack_client.files_upload_v2(
#             channels=data["channel_id"],
#             file=csv_filename,
#             title="검색 트렌드 결과"
#         )
#         return jsonify({"text": "CSV 파일을 업로드했습니다."}), 200
#     except SlackApiError as e:
#         return jsonify({"text": f"Slack 파일 업로드 실패: {e.response['error']}"}), 200
@app.route("/slack/search_trend", methods=["POST"])
def slack_search_trend():
    print("[LOG] Slack 요청 받음")  # Slack 요청을 받았는지 확인
    print("Request Form:", request.form)

    data = request.form
    command_text = data.get("text", "").split()

    if len(command_text) < 4:
        print("[LOG] 잘못된 요청 형식")
        return jsonify({"text": "올바른 형식: /search_trend keyword1 keyword2 days device"}), 200

    keyword1, keyword2, days, device = command_text[0], command_text[1], int(command_text[2]), command_text[3]

    print(f"[LOG] 키워드1: {keyword1}, 키워드2: {keyword2}, 기간: {days}, 디바이스: {device}")

    result_df = calculate_search_trend(keyword1, keyword2, days_ago=days, device=device)

    if result_df is None:
        print("[LOG] 데이터 없음")
        return jsonify({"text": "데이터를 가져오지 못했습니다."}), 200

    result_json = result_df.to_json(orient="records", force_ascii=False)

    print("[LOG] 검색 트렌드 결과 전송 완료")

    return jsonify({"text": f"🔍 검색 트렌드 결과:\n```{result_json}```"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
