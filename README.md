
## Slack 네이버 키워드 검색 봇
이 프로젝트는 Slack에서 네이버 검색광고 API를 이용해 연관 키워드를 검색하는 슬랙봇입니다.

## 🚀 기능
- Slack에서 `/keywords` 입력 시, 네이버 검색광고 API에서 관련 키워드 검색
- 검색된 키워드를 Slack 메시지로 반환

## 🔧 설치 방법
1. `app.py`, `requirements.txt`, `Procfile` 파일을 GitHub에 업로드
2. Render에서 Web Service 배포
3. Slack Slash Command 설정 후 사용

## 📌 환경 변수 설정
`.env` 파일에 아래 정보를 추가 (Render에서는 직접 환경 변수로 설정)
