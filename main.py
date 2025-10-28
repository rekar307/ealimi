import os
import argparse
from dotenv import load_dotenv
from crawling import *
from notify_mail import send_gmail
from notify_chat import send_synology_chat

load_dotenv()
# load_dotenv(".env2", override=True)

EALIMI_ID = os.getenv("EALIMI_ID")
EALIMI_PW = os.getenv("EALIMI_PW")
RECEIVER_MAIL = ""  # . os.getenv("RECEIVER_MAIL")
EALIMI_URL = os.getenv("EALIMI_URL")
STUDENT_NAME = os.getenv("STUDENT_NAME")
CHAT_WEBHOOK_URL = os.getenv("CHAT_WEBHOOK_URL")


def get_date(input_date=None):
    if input_date:
        return {input_date}
    return {datetime.now().strftime("%Y-%m-%d")}


def send_email(receiver_email, subject, body):
    if not receiver_email:
        print("❌ RECEIVER_MAIL이 설정되지 않았습니다. 메일을 보내지 않습니다.")
        return
    try:
        ret = send_gmail(receiver_email, subject, body)
        if ret:
            print("✅ 오늘 알림장 메일 발송 완료")
    except Exception as e:
        print(f"메일 발송 실패: {e}")


def send_chat(chat_webhook_url, subject, body):
    if not chat_webhook_url:
        print("❌ CHAT_WEBHOOK_URL이 설정되지 않았습니다. 메시지를 보내지 않습니다.")
        return
    try:
        ret = send_synology_chat(chat_webhook_url, subject, body)
        if ret:
            print("✅ 오늘 알림장 Chat Bot 발송 완료")
    except Exception as e:
        print(f"Chat Bot 메시지 발송 실패: {e}")


def save_data(outpath, subject, body):
    if outpath:
        try:
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(f"{subject}\n{body}\n")
            print(f"✅ 데이터가 {outpath}에 저장되었습니다.")
        except Exception as e:
            print(f"데이터 저장 실패: {e}")


def print_data(subject, body):
    print("=" * 50)
    print(subject)
    print(body)
    print("=" * 50)


def run(outpath=None, input_date=None):
    board_url = EALIMI_URL
    login_id = EALIMI_ID
    login_pw = EALIMI_PW
    student_name = STUDENT_NAME
    email = RECEIVER_MAIL
    chat_webhook_url = CHAT_WEBHOOK_URL
    driver = init_web_driver()

    try:
        login(driver, login_id, login_pw)
        select_student(driver, student_name)
        notices = crawling_notices(driver, board_url)
        my_date = get_date(input_date)
        found = False

        for notice in notices:
            found = find_page(driver, notice, my_date)
            if found:
                break

        subject, body = create_cont(driver, found)
        send_email(email, subject, body)
        # send_chat(chat_webhook_url, subject, body)
        save_data(outpath, subject, body)
        print_data(subject, body)

    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outpath", type=str, help="저장할 파일 경로 (./data/2025-10-02.txt)"
    )
    parser.add_argument(
        "--date", type=str, help="조회할 날짜 (YYYY-MM-DD)", default=None
    )
    args = parser.parse_args()
    run(args.outpath, args.date)
