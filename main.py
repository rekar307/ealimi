from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
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
RECEIVER_MAIL = os.getenv("RECEIVER_MAIL")
EALIMI_URL1 = os.getenv("EALIMI_URL1")  # 알림장/커뮤니티 주소
EALIMI_URL2 = os.getenv("EALIMI_URL2")

# 학생 선택용 (있으면 ID가 가장 안정적)
STUDENT_ID = os.getenv("STUDENT_ID")  # 예: "12145907"
STUDENT_NAME = os.getenv("STUDENT_NAME", "김은재")

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
# Selenium 유틸
# -------------------------
def accept_alert_if_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        return True
    except TimeoutException:
        return False


def open_student_dropdown(driver):
    # 좌상단 학교명 옆 드롭다운
    btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "orgcontents"))
    )
    btn.click()
    # 드롭다운 항목 나타날 때까지 대기
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "a.person_stat_a"))
    )


def select_student(driver, sid=None, name=None):
    open_student_dropdown(driver)

    if sid:
        # href="javascript:fnSessChk('12145907');" 형태를 부분 매칭
        locator = (By.XPATH, f"//a[contains(@href, \"fnSessChk('{sid}')\")]")
    else:
        # 항목 <a> 내부 텍스트가 span 분할일 수 있으니 .(점)으로 포함 검색
        safe = name or ""
        locator = (By.XPATH, f"//a[contains(., '{safe}')]")

    link = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(locator))
    # 클릭 가림 방지
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(locator)).click()
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
        TimeoutException,
    ):
        # 겹침/가림 이슈 시 JS 클릭
        driver.execute_script("arguments[0].click();", link)

    # 선택 직후 알럿이 뜨면 수락
    accept_alert_if_present(driver, timeout=2)


# -------------------------
# Selenium으로 알림장 크롤링
# -------------------------
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
# 알럿이 떠도 자동 수락 (Selenium 4 capability)
options.set_capability("unhandledPromptBehavior", "accept")

driver = webdriver.Chrome(options=options)

today = datetime.now().strftime("%Y-%m-%d")
# 사이트 날짜 표기가 다를 수 있어 후보를 몇 개 만든다.
today_candidates = {
    datetime.now().strftime("%Y-%m-%d"),
    datetime.now().strftime("%Y.%m.%d"),
    datetime.now().strftime("%Y/%m/%d"),
}

board_url = EALIMI_URL1

try:
    # 로그인
    driver.get("https://www.ealimi.com/Member/SignIn")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
    driver.find_element(By.ID, "id").send_keys(EALIMI_ID)
    driver.find_element(By.ID, "pw").send_keys(EALIMI_PW)
    driver.find_element(By.ID, "signInSubmitBtn").click()

    # 로그인 직후 알럿 처리 (있을 수도 있음)
    accept_alert_if_present(driver, timeout=5)

    # 학생 선택 (ID가 있으면 ID로, 없으면 이름으로)
    select_student(driver, sid=STUDENT_ID, name=STUDENT_NAME)

    # 알림장 페이지 이동
    driver.get(board_url)
    time.sleep(1)
    # 접근 불가 알럿 뜨면 중단
    if accept_alert_if_present(driver, timeout=3):
        raise SystemExit("열람 가능한 게시판이 없습니다. (권한/대상 선택 확인)")

    # 알림장 목록 로딩 대기
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#ListContent"))
    )

    notices = driver.find_elements(
        By.CSS_SELECTOR, "#ListContent .gb_lr.box_list.type_list"
    )

    found = False
    for notice in notices:
        reg_dt = notice.find_element(By.CSS_SELECTOR, ".content_reg_dt").text.strip()
        if any(d in reg_dt for d in today_candidates):
            link = notice.find_element(By.CSS_SELECTOR, ".content_title a")
            link.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#EditorHtml"))
            )

            title = driver.find_element(By.CSS_SELECTOR, ".article_tit").text
            content = driver.find_element(By.CSS_SELECTOR, "#EditorHtml").text

            body = f"제목: {title}\n\nURL: {driver.current_url}\n\n본문:\n{content}"
            send_gmail(
                RECEIVER_MAIL,
                f"[e알리미] 오늘 {datetime.now().strftime('%Y-%m-%d')} 알림장 - {title}",
                body,
            )

            print("오늘 알림장 메일 발송 완료 ✅")
            found = True
            break

    if not found:
        print("오늘 날짜 알림장이 없습니다.")

finally:
    driver.quit()
