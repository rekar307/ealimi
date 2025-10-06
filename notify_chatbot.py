import json
import requests

def send_synology_chat(webhook_url, subject, body, use_https=False):
    """
    Synology Chat Webhook 메시지 전송 함수
    - webhook_url: Chat 통합에서 생성된 URL
    - subject: 제목
    - body: 본문 내용
    - use_https=True 시 5001 포트 사용 + SSL 검증 끔
    """

    payload = {"text": f"{subject}\n\n{body}"}

    try:
        res = requests.post(
            webhook_url,
            data={"payload": json.dumps(payload, ensure_ascii=False)},
            timeout=10,
            verify=False  # HTTPS인 경우 verify=False
        )

        print("=== Synology Chat Webhook Debug ===")
        print("Request URL:", res.request.url)
        print("Request Body:", res.request.body)
        print("Status Code:", res.status_code)
        print("Response Text:", res.text)
        print("===================================")

        res.raise_for_status()
        print("✅ 메시지 전송 성공!")
        return True

    except requests.RequestException as e:
        print("❌ 요청 중 오류 발생:", e)
        return False
