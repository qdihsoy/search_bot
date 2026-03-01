import os
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# 設定
TARGET_URL = "https://fujiikaze.com/news-article/"
USER_ID = os.getenv('LINE_USER_ID')
FILE_PATH = "last_fujii_news.txt"

configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

def send_line(message):
    """LINEにプッシュ通知を送る"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(PushMessageRequest(
            to=USER_ID,
            messages=[TextMessage(text=message)]
        ))

def check_fujii_kaze_news():
    print(f"--- チェック開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    try:
        # 1. サイトのHTMLを取得
        headers = {'User-Agent': 'Mozilla/5.0'} # ロボット拒否対策
        res = requests.get(TARGET_URL, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 2. 最新ニュースのタイトルと日付を特定
        # ニュースリストの最初（一番上）の項目を取得
        latest_news_item = soup.select_one(".news-list li a")
        
        if not latest_news_item:
            print("ニュースが見つかりませんでした。サイトの構造が変わった可能性があります。")
            return

        # タイトルと日付を抽出
        date_text = latest_news_item.select_one("span").get_text().strip()
        title_text = latest_news_item.select_one("p").get_text().strip()
        current_news = f"{date_text} {title_text}"
        
        print(f"現在の最新ニュース: {current_news}")

        # 3. 前回の保存内容と比較
        last_news = ""
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                last_news = f.read().strip()

        if current_news != last_news:
            print("✨ 新着ニュースを発見！")
            # LINE通知
            msg = f"🍃 藤井 風 公式サイト更新！\n\n{current_news}\n\nURL: {TARGET_URL}"
            send_line(msg)
            
            # 4. 新しい内容をファイルに保存
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.write(current_news)
        else:
            print("変化なし。")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    check_fujii_kaze_news()