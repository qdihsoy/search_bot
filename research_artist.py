import os
import glob
from google import genai
from google.genai import types
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

def get_latest_report(artist):
    """既存の report_{artist}_*.txt の中で一番新しいファイルの内容を読み込む"""
    files = glob.glob(f"report_{artist}_*.txt")
    if not files:
        return ""

    latest_file = sorted(files)[-1]
    print(f"📄 前回の参照ファイル: {latest_file}")
    with open(latest_file, "r", encoding="utf-8") as f:
        return f.read().strip()

def delete_old_reports():
    """14日以上前のレポートファイルを削除する"""
    print("--- 古いレポートの整理開始 ---")
    files = glob.glob("report_*.txt")
    threshold_date = datetime.now() - timedelta(days=14)
    
    for f in files:
        try:
            parts = f.replace(".txt", "").split("_")
            date_str = "_".join(parts[-3:]) 
            file_date = datetime.strptime(date_str, '%Y_%m_%d')
            
            if file_date < threshold_date:
                os.remove(f)
                print(f"🗑️ 古いレポートを削除しました: {f}")
        except Exception as e:
            print(f"⏩ スキップ (解析不能): {f}")

ARTISTS = ["藤井風", "KingGnu", "BackNumber", "TOMOO", "NewJeans", "乃木坂46"]

def search_and_report():
    for artist in ARTISTS:
        print("--- Geminiによる最新情報リサーチ開始 ---")
        
        today_str = datetime.now().strftime('%Y_%m_%d')
        current_filename = f"report_{artist}_{today_str}.txt"
        
        last_report = get_latest_report(artist)

        prompt = f"""
        {artist}に関する最新情報をGoogle検索で調査してください。
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
            send_line(f" {artist} 最新リサーチ報告\n\n{current_report}")

            with open(current_filename, "w", encoding="utf-8") as f:
                f.write(current_report)
        else:
            print("変化なし。生存確認メッセージを送ります。")
            send_line(f" 今日の{artist}リサーチ：新着情報はありませんでした。ボットは正常に稼働中")

if __name__ == "__main__":
    delete_old_reports()
    search_and_report()