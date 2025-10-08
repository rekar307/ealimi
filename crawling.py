import time
import tempfile
from datetime import datetime
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


def init_web_driver():
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.set_capability("unhandledPromptBehavior", "accept")
    options.add_argument("--headless")  # 화면 없이 실행
    options.add_argument("--no-sandbox")  # 권한 문제 해결
    options.add_argument("--disable-dev-shm-usage")  # 메모리 문제 해결
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")  # 임시 디렉토리 사용

    driver = webdriver.Chrome(options=options)
    return driver


def login(driver, user_id, password):
    driver.get("https://www.ealimi.com/Member/SignIn")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
    driver.find_element(By.ID, "id").send_keys(user_id)
    driver.find_element(By.ID, "pw").send_keys(password)
    driver.find_element(By.ID, "signInSubmitBtn").click()

    # 로그인 직후 알럿 처리 (있을 수도 있음)
    accept_alert_if_present(driver, timeout=2)


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


def accept_alert_if_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        return True
    except TimeoutException:
        return False


def select_student(driver, name=None):
    open_student_dropdown(driver)

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

    accept_alert_if_present(driver, timeout=2)


def crawling_notices(driver, board_url):
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

    # 알림장 list 반환
    notices = driver.find_elements(
        By.CSS_SELECTOR, "#ListContent .gb_lr.box_list.type_list"
    )
    return notices


def find_page(driver, notice, date_list):
    register_date = notice.find_element(By.CSS_SELECTOR, ".content_reg_dt").text.strip()

    found = False
    if any(day in register_date for day in date_list):
        link = notice.find_element(By.CSS_SELECTOR, ".content_title a")
        link.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#EditorHtml"))
        )
        found = True
    return found


def create_cont(driver, found):
    if found:
        title = driver.find_element(By.CSS_SELECTOR, ".article_tit").text
        subject = (
            f"[e알리미] 오늘 {datetime.now().strftime('%Y-%m-%d')} 알림장 - {title}"
        )
        content = driver.find_element(By.CSS_SELECTOR, "#EditorHtml").text
        body = f"제목: {title}\n\n본문:\n{content}\n\nURL: {driver.current_url}"
    else:
        subject = f"[e알리미] 오늘 {datetime.now().strftime('%Y-%m-%d')} 알림장 - 없음"
        body = "오늘 날짜 알림장이 없습니다."

    return subject, body
