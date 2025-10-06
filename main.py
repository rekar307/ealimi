import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
from notify_mail import send_gmail
from notify_chatbot import send_synology_chat


load_dotenv()

EALIMI_ID = os.getenv("EALIMI_ID")
EALIMI_PW = os.getenv("EALIMI_PW")
RECEIVER_MAIL = os.getenv("RECEIVER_MAIL")
EALIMI_URL1 = os.getenv("EALIMI_URL1")
EALIMI_URL2 = os.getenv("EALIMI_URL2")
STUDENT_ID = os.getenv("STUDENT_ID")
STUDENT_NAME = os.getenv("STUDENT_NAME")
CHAT_WEBHOOK_URL = os.getenv("CHAT_WEBHOOK_URL")

# Selenium
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

def login(driver, user_id, password):
    driver.get("https://www.ealimi.com/Member/SignIn")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
    driver.find_element(By.ID, "id").send_keys(user_id)
    driver.find_element(By.ID, "pw").send_keys(password)
    driver.find_element(By.ID, "signInSubmitBtn").click()
    
    # 로그인 직후 알럿 처리 (있을 수도 있음)
    accept_alert_if_present(driver, timeout=2)

def main():
    options = Options()
    driver = webdriver.Chrome(options=options)
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.set_capability("unhandledPromptBehavior", "accept")
    driver = webdriver.Chrome(options=options)
    board_url = EALIMI_URL1

    try:
        login(driver, EALIMI_ID, EALIMI_PW)

        # 학생 선택 (ID가 있으면 ID로, 없으면 이름으로)
        select_student(driver, sid=STUDENT_ID, name=STUDENT_NAME)

        # 알림장 페이지 이동
        driver.get(board_url)
        time.sleep(1)

        # 접근 불가 알럿 뜨면 중단
        if accept_alert_if_present(driver, timeout=2):
            raise SystemExit("열람 가능한 게시판이 없습니다. (권한/대상 선택 확인)")

        # 알림장 목록 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ListContent"))
        )

        # 오늘 날짜 알림장 찾기
        notices = driver.find_elements(
            By.CSS_SELECTOR, "#ListContent .gb_lr.box_list.type_list"
        )

        # 오늘 날짜 후보군 생성 (형식 다양)
        today = datetime.now().strftime("%Y-%m-%d")
        today_candidates = {
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y.%m.%d"),
            datetime.now().strftime("%Y/%m/%d"),
        }
        
        # 테스트
        if __debug__:
            today_candidates.add("2025-10-02")
            print(f"오늘 날짜 후보군: {today_candidates}")

        found = False
        for notice in notices:
            reg_dt = notice.find_element(By.CSS_SELECTOR, ".content_reg_dt").text.strip()
            if any(d in reg_dt for d in today_candidates):
                link = notice.find_element(By.CSS_SELECTOR, ".content_title a")
                link.click()

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#EditorHtml"))
                )
                
                # 본문 내용 추출
                title = driver.find_element(By.CSS_SELECTOR, ".article_tit").text
                content = driver.find_element(By.CSS_SELECTOR, "#EditorHtml").text
                body = f"제목: {title}\n\nURL: {driver.current_url}\n\n본문:\n{content}"
                print(body)

                # # 메일 발송
                # send_gmail(
                #     RECEIVER_MAIL,
                #     f"[e알리미] 오늘 {datetime.now().strftime('%Y-%m-%d')} 알림장 - {title}",
                #     body,
                # )
                # print("오늘 알림장 메일 발송 완료 ✅")
                # found = True

                # Chat Bot 메시지 발송
                if CHAT_WEBHOOK_URL:
                    send_synology_chat(
                        CHAT_WEBHOOK_URL,
                        f"[e알리미] 오늘 {datetime.now().strftime('%Y-%m-%d')} 알림장 - {title}",
                        body,
                    )
                    print("오늘 알림장 Synology Chat 메시지 발송 완료 ✅")
                else:
                    print("CHAT_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

                # 종료
                break

        if not found:
            print("오늘 날짜 알림장이 없습니다.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
