import os
import glob
from google import genai
from google.genai import types
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
LINE_USER_ID = os.getenv('LINE_USER_ID')
configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

client = genai.Client(api_key=GEMINI_API_KEY)

def send_line(message):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(PushMessageRequest(
            to=LINE_USER_ID,
            messages=[TextMessage(text=message)]
        ))

def get_latest_report():
    """既存の report_fk_*.txt の中で一番新しいファイルの内容を読み込む"""
    files = glob.glob("report_fk_*.txt")
    if not files:
        return ""

    latest_file = sorted(files)[-1]
    print(f"📄 前回の参照ファイル: {latest_file}")
    with open(latest_file, "r", encoding="utf-8") as f:
        return f.read().strip()

def search_and_report():
    print("--- Geminiによる最新情報リサーチ開始 ---")
    
    today_str = datetime.now().strftime('%Y_%m_%d')
    current_filename = f"report_fk_{today_str}.txt"
    
    last_report = get_latest_report()

    prompt = f"""
    藤井 風（Fujii Kaze）に関する最新情報をGoogle検索で調査してください。
    特に「新曲のリリース」「ライブ・ツアーの開催」「チケットの販売（先行予約含む）」に焦点を当ててください。
    
    【ルール】
    ・今日（{today_str}）時点での最新ニュースを3行程度で箇条書きにして。
    ・関連する公式サイトや公式ニュースのURLを必ず1つ以上含めて。
    ・もし前回（以下）の内容と本質的に同じ場合は「特になし」と答えて。
    
    前回知っていた情報：
    {last_report}
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    current_report = response.text.strip()
    print(f"Geminiの回答: \n{current_report}")

    if "特になし" not in current_report and current_report != last_report:
        print(f"✨ 新着あり！ファイル {current_filename} を作成し、LINEに送ります。")
        send_line(f"🍃 藤井 風 最新リサーチ報告\n\n{current_report}")

        with open(current_filename, "w", encoding="utf-8") as f:
            f.write(current_report)
    else:
        print("変化なし、または新着情報なし。")

if __name__ == "__main__":
    search_and_report()