import os
import glob
from google import genai
from google.genai import types
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, TextMessage, BroadcastRequest # BroadcastRequestを追加
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
LINE_USER_ID = os.getenv('LINE_USER_ID')
configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

client = genai.Client(api_key=GEMINI_API_KEY)

def send_line(message):
    """友達全員に一括送信（Broadcast）"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.broadcast(BroadcastRequest(
            messages=[TextMessage(text=message)]
        ))

def get_latest_report_info(artist):
    files = glob.glob(f"report_{artist}_*.txt")
    if not files:
        return None, ""
    latest_file = sorted(files)[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        return latest_file, f.read().strip()

ARTISTS = ["藤井風", "KingGnu", "BackNumber", "TOMOO", "NewJeans", "乃木坂46"]

def search_and_report():
    reports_for_line = []
    
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
        {old_content[:1000]}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        current_report = response.text.strip()
        
        if "特になし" not in current_report:
            print(f"✨ {artist}: 新着あり")
            separator = "\n\n" + "="*30 + "\n\n"
            header = f"📅 {today_display_str} のリサーチ\n"
            updated_content = f"{header}{current_report}{separator}{old_content}"
            
            with open(new_filename, "w", encoding="utf-8") as f:
                f.write(updated_content.strip())
            
            if old_filename and old_filename != new_filename:
                os.remove(old_filename)

            reports_for_line.append(f"🌟 【{artist}】\n{current_report}")
        else:
            print(f"✅ {artist}: 変化なし")
            if old_filename and old_filename != new_filename:
                os.rename(old_filename, new_filename)
            
            reports_for_line.append(f"✅ 【{artist}】\n新着なし（稼働中）")

    if reports_for_line:
        final_message = f"📢 本日のアーティストリサーチ結果\n({today_display_str})\n\n" + "\n\n" + "\n".join(reports_for_line)

        if len(final_message) > 4800:
            final_message = final_message[:4800] + "\n...以下省略"
            
        send_line(final_message)
        print("🚀 LINEを一括送信しました。")

if __name__ == "__main__":
    search_and_report()