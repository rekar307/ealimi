import os
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


def get_date():
    today = {
        datetime.now().strftime("%Y-%m-%d"),
        # datetime.now().strftime("%Y.%m.%d"),
        # datetime.now().strftime("%Y/%m/%d"),
    }

    # if __debug__:
    #     today.add("2025-10-02")
    #     print(f"테스트 날짜 추가: {today}")

    return today


def send_email(receiver_email, subject, body):
    if not receiver_email:
        print("RECEIVER_MAIL이 설정되지 않았습니다. 메일을 보내지 않습니다.")
        return
    try:
        send_gmail(receiver_email, subject, body)
        print("오늘 알림장 메일 발송 완료 ✅")
    except Exception as e:
        print(f"메일 발송 실패: {e}")


def send_chat(webhook_url, subject, message):
    if not webhook_url:
        print("CHAT_WEBHOOK_URL이 설정되지 않았습니다. 메시지를 보내지 않습니다.")
        return
    try:
        send_synology_chat(webhook_url, subject, message)
        print("오늘 알림장 Chat Bot 발송 완료 ✅")
    except Exception as e:
        print(f"Chat Bot 메시지 발송 실패: {e}")


def main():
    driver = init_web_driver()
    board_url = EALIMI_URL
    login_id = EALIMI_ID
    login_pw = EALIMI_PW
    student_name = STUDENT_NAME
    email = RECEIVER_MAIL
    chat_url = CHAT_WEBHOOK_URL

    try:
        login(driver, login_id, login_pw)
        select_student(driver, student_name)
        notices = crawling_notices(driver, board_url)
        my_date = get_date()

        for notice in notices:
            found = find_page(driver, notice, my_date)
            if found:
                break

        subject, body = create_cont(driver, found)
        send_email(email, subject, body)
        send_chat(chat_url, subject, body)
        print("=" * 50)
        print(subject)
        print(body)
        print("=" * 50)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
