from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from datetime import datetime
from dotenv import load_dotenv
import time
import os

# Gmail 관련
from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

load_dotenv()

EALIMI_ID = os.getenv("EALIMI_ID")
EALIMI_PW = os.getenv("EALIMI_PW")

# -------------------------
# Gmail API 인증 함수
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("gmail", "v1", credentials=creds)
    return service


def send_gmail(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


# -------------------------
# Selenium으로 알림장 크롤링
# -------------------------
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(options=options)

EALIMI_ID = os.getenv("EALIMI_ID")
EALIMI_PW = os.getenv("EALIMI_PW")

today = datetime.now().strftime("%Y-%m-%d")
board_url = "https://www.ealimi.com/board?code=18&CC_ID=143896&IsApp=1"

try:
    # 로그인
    driver.get("https://www.ealimi.com/Member/SignIn")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
    driver.find_element(By.ID, "id").send_keys(EALIMI_ID)
    driver.find_element(By.ID, "pw").send_keys(EALIMI_PW)
    driver.find_element(By.ID, "signInSubmitBtn").click()

    # alert 처리
    WebDriverWait(driver, 10).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    alert.accept()

    # 알림장 페이지 이동
    driver.get(board_url)
    time.sleep(2)

    # 알림장 목록
    notices = driver.find_elements(
        By.CSS_SELECTOR, "#ListContent .gb_lr.box_list.type_list"
    )

    found = False
    for notice in notices:
        reg_dt = notice.find_element(By.CSS_SELECTOR, ".content_reg_dt").text.strip()
        if today in reg_dt:
            link = notice.find_element(By.CSS_SELECTOR, ".content_title a")
            link.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#EditorHtml"))
            )

            title = driver.find_element(By.CSS_SELECTOR, ".article_tit").text
            content = driver.find_element(By.CSS_SELECTOR, "#EditorHtml").text

            body = f"제목: {title}\n\nURL: {board_url}\n\n본문:\n{content}"
            send_gmail("rekar307@gmail.com", f"[e알리미] 오늘 알림장 - {title}", body)

            print("오늘 알림장 메일 발송 완료 ✅")
            found = True
            break

    if not found:
        print("오늘 날짜 알림장이 없습니다.")

finally:
    driver.quit()
