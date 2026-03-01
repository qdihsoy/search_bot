import os
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TARGET_URL = "https://fujiikaze.com/news-article/"
USER_ID = os.getenv('LINE_USER_ID')
FILE_PATH = "last_fujii_news.txt"

configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

def send_line(message):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(PushMessageRequest(
            to=USER_ID,
            messages=[TextMessage(text=message)]
        ))

def check_fujii_kaze_news():
    print(f"--- チェック開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        res = requests.get(TARGET_URL, headers=headers)
        res.raise_for_status()
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 【最新の住所を特定】
        # 1. ニュースのリストを取得
        first_item = soup.select_one(".fk-news-archive__item")
        
        if not first_item:
            print("DEBUG: ニュース項目 (.fk-news-archive__item) が見つかりませんでした。")
            return

        # 2. 日付とタイトルの抽出
        # 日付は <span class="--date"> の中
        date_tag = first_item.select_one(".--date")
        date_text = date_tag.get_text().strip() if date_tag else ""
        
        # タイトルは <a> タグの中にあるテキスト（imgやspanを除いた部分）
        link_tag = first_item.select_one(".fk-news-archive__link")
        if link_tag:
            # get_text(strip=True) だと中身が全部繋がるので、
            # 日付部分（span）を一時的に除外してテキストだけを抽出
            full_text = link_tag.get_text().replace(date_text, "").strip()
            # 余計な記号などを掃除
            title_text = full_text.split('\n')[0].strip() 
            current_news = f"{date_text} {title_text}"
        else:
            current_news = first_item.get_text().strip()

        print(f"取得成功: {current_news}")

        # --- 比較と通知の処理 ---
        last_news = ""
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                last_news = f.read().strip()

        if current_news != last_news:
            print("✨ 新着あり！")
            send_line(f"🍃 藤井 風 公式サイト更新！\n\n{current_news}\n\nURL: {TARGET_URL}")
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.write(current_news)
        else:
            print("変化なし。")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    check_fujii_kaze_news()