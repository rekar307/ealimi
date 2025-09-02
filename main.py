from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from datetime import datetime
from dotenv import load_dotenv
import time
import os

load_dotenv()

EALIMI_ID = os.getenv("EALIMI_ID")
EALIMI_PW = os.getenv("EALIMI_PW")

options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # 디버깅할 땐 주석 처리
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(options=options)

try:
    # 1. 로그인 페이지 접속
    driver.get("https://www.ealimi.com/Member/SignIn")

    # 2. 아이디/비번 입력칸 기다리기
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))

    # 3. 아이디/비번 입력
    driver.find_element(By.ID, "id").send_keys(EALIMI_ID)
    driver.find_element(By.ID, "pw").send_keys(EALIMI_PW)

    # 로그인 버튼 클릭
    driver.find_element(By.ID, "signInSubmitBtn").click()

    # alert 대기 후 처리
    WebDriverWait(driver, 10).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    print("로그인 알림:", alert.text)  # "로그인 요청을 정상적으로 처리하였습니다."
    alert.accept()  # 확인 버튼 누르기

    # 5. 로그인 후 알림장 페이지 이동
    WebDriverWait(driver, 10).until(EC.url_contains("Main"))
    driver.get("https://www.ealimi.com/board?code=18&CC_ID=143896&IsApp=1")

    time.sleep(3)
    print(driver.page_source[:2000])  # 페이지 일부 출력

    # # 날짜별 알림장 목록 가져오기
    # notices = driver.find_elements(
    #     By.CSS_SELECTOR, "#ListContent .gb_lr.box_list.type_list"
    # )

    # result = []
    # for notice in notices:
    #     title = notice.find_element(By.CSS_SELECTOR, ".content_title a.title_link").text
    #     writer = notice.find_element(By.CSS_SELECTOR, ".content_reg_nm").text
    #     reg_dt = notice.find_element(By.CSS_SELECTOR, ".content_reg_dt").text
    #     views = notice.find_element(By.CSS_SELECTOR, ".box_desc .cnt").text

    #     result.append(
    #         {"title": title, "writer": writer, "date": reg_dt, "views": views}
    #     )

    # # 확인 출력
    # for r in result:
    #     print(f"[{r['date']}] {r['title']} (작성자: {r['writer']}, 조회: {r['views']})")

    # 오늘 날짜 문자열 (YYYY-MM-DD 형식)
    today = datetime.now().strftime("%Y-%m-%d")

    # 알림장 목록 다시 가져오기
    notices = driver.find_elements(
        By.CSS_SELECTOR, "#ListContent .gb_lr.box_list.type_list"
    )

    for notice in notices:
        reg_dt = notice.find_element(By.CSS_SELECTOR, ".content_reg_dt").text.strip()
        if today in reg_dt:
            # 제목 링크 안전하게 찾기
            link = notice.find_element(By.CSS_SELECTOR, ".content_title a")

            # 클릭
            link.click()

            # 팝업 본문 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#EditorHtml"))
            )

            # 제목 + 본문 추출
            title = driver.find_element(By.CSS_SELECTOR, ".article_tit").text
            content = driver.find_element(By.CSS_SELECTOR, "#EditorHtml").text

            print("오늘 알림장 제목:", title)
            print("오늘 알림장 본문:\n", content)

            # 닫기 버튼이 있다면 닫기
            try:
                driver.find_element(By.CSS_SELECTOR, ".btn_layer_close").click()
            except:
                pass

            break

finally:
    driver.quit()
