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
        res.raise_for_status() # 接続エラーがあればここで止める
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 【修正】より確実な探し方に変更
        # 1. まず <ul> タグを探す
        news_list = soup.find('ul') 
        
        # 2. その中の最初の <li> を探す
        if news_list:
            first_item = news_list.find('li')
        else:
            print("DEBUG: ulタグ自体が見つかりませんでした")
            # サイトのHTMLの一部を表示して診断
            print(f"HTML抜粋: {res.text[:500]}") 
            return

        if not first_item:
            print("DEBUG: liタグが見つかりませんでした")
            return

        # タイトルと日付を抽出
        # spanの中に日付、pの中にタイトルがある構造を狙う
        date_tag = first_item.find('span')
        title_tag = first_item.find('p')

        if date_tag and title_tag:
            current_news = f"{date_tag.get_text().strip()} {title_tag.get_text().strip()}"
        else:
            # もしspan/pがなくてもaタグの中身を全部取る
            current_news = first_item.get_text().strip().replace('\n', ' ')

        print(f"取得成功: {current_news}")

        # 比較処理
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