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

def get_latest_report_info(artist):
    """
    既存の report_{artist}_*.txt を探し、
    (ファイル名, 中身) のセットを返す。なければ (None, "")
    """
    files = glob.glob(f"report_{artist}_*.txt")
    if not files:
        return None, ""

    latest_file = sorted(files)[-1]
    print(f"📄 既存のレポートを読み込みます: {latest_file}")
    with open(latest_file, "r", encoding="utf-8") as f:
        return latest_file, f.read().strip()

ARTISTS = ["藤井風", "KingGnu", "BackNumber", "TOMOO", "NewJeans", "乃木坂46"]

def search_and_report():
    for artist in ARTISTS:
        print(f"--- {artist} のリサーチ開始 ---")
        
        today_dt = datetime.now()
        today_filename_str = today_dt.strftime('%Y_%m_%d')
        today_display_str = today_dt.strftime('%Y/%m/%d')
        
        new_filename = f"report_{artist}_{today_filename_str}.txt"
        
        old_filename, old_content = get_latest_report_info(artist)

        prompt = f"""
        {artist}に関する最新情報をGoogle検索で調査してください。
        特に「新曲のリリース」「ライブ・ツアーの開催」「チケットの販売（先行予約含む）」に焦点を当ててください。
        
        【ルール】
        ・今日（{today_display_str}）時点での最新ニュースを3行程度で箇条書きにして。
        ・関連する公式サイトや公式ニュースのURLを必ず1つ以上含めて。
        ・もし前回のリサーチ結果（以下）と本質的に同じ場合は「特になし」と答えて。
        
        前回のリサーチ結果：
        {old_content[:1000]}  # 長くなりすぎないよう直近1000文字程度を参照
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

        if "特になし" not in current_report:
            print(f"✨ 新着あり！{new_filename} を更新し、LINEに送ります。")
            
            separator = "\n\n" + "="*30 + "\n\n"
            header = f"📅 {today_display_str} のリサーチ\n"
            
            updated_content = f"{header}{current_report}{separator}{old_content}"
            
            with open(new_filename, "w", encoding="utf-8") as f:
                f.write(updated_content.strip())
            
            if old_filename and old_filename != new_filename:
                os.remove(old_filename)
                print(f"🗑️ 旧ファイルを削除しました: {old_filename}")

            send_line(f"【{artist}】最新リサーチ報告\n\n{current_report}")

        else:
            print(f"✅ {artist}：変化なし。")
            if old_filename and old_filename != new_filename:
                os.rename(old_filename, new_filename)
                print(f"♻️ 内容不変のためファイル名のみ更新: {new_filename}")
            
            send_line(f"今日の{artist}リサーチ：新着情報はありませんでした。")

if __name__ == "__main__":
    search_and_report()