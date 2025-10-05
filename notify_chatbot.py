import requests, json

def send_synology_chat(webhook_url, subject, body):
    payload = {"text": f"{subject}\n\n{body}"}

    try:
        res = requests.post(
            webhook_url,
            data={"payload": json.dumps(payload, ensure_ascii=False)},
            timeout=10,
        )

        # 디버깅 출력
        print("=== Synology Chat Webhook Debug ===")
        print("Request URL:", res.request.url)
        print("Request Body:", res.request.body)
        print("Status Code:", res.status_code)
        print("Response Headers:", dict(res.headers))
        print("Response Text:", res.text)
        print("===================================")

        res.raise_for_status()
        return True

    except requests.RequestException as e:
        print("요청 중 오류 발생:", e)
        return False
