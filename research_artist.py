import os
import glob
from google import genai
from google.genai import types
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, TextMessage, BroadcastRequest
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
LINE_USER_ID = os.getenv('LINE_USER_ID')
configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

client = genai.Client(api_key=GEMINI_API_KEY)
FOLDER = "reports_artist"

def send_line(message):
    """友達全員に一括送信（Broadcast）"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.broadcast(BroadcastRequest(
            messages=[TextMessage(text=message)]
        ))

def get_latest_report_info(artist):
    files = glob.glob(f"{FOLDER}/report_{artist}_*.txt") 
    if not files: return None, ""
    latest_file = sorted(files)[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        return latest_file, f.read().strip()

ARTISTS = ["藤井風", "KingGnu", "BackNumber", "TOMOO", "NewJeans", "乃木坂46"]

def search_and_report():
    os.makedirs(FOLDER, exist_ok=True)
    no_updates_artists = []
    has_updates_reports = []
    
    today_dt = datetime.now()
    today_display_str = today_dt.strftime('%Y/%m/%d')
    today_filename_str = today_dt.strftime('%Y_%m_%d')

    for artist in ARTISTS:
        print(f"--- {artist} のリサーチ開始 ---")
        new_filename = f"{FOLDER}/report_{artist}_{today_filename_str}.txt"
        old_filename, old_content = get_latest_report_info(artist)

        prompt = f"""
        {artist}に関する最新情報をGoogle検索で調査してください。
        特に「新曲のリリース」「ライブ・ツアーの開催」「チケットの販売（先行予約含む）」に焦点を当ててください。
        
        【前回の調査内容】
        {old_content[:2000]}
        
        【注意事項】
        「前回の調査内容」と比較して、**「全く新しい事実（差分）」がある場合のみ**、その差分について報告してください。
        以下の場合は、迷わず「特になし」と回答してください。
        - 前回の内容と、日付・場所・タイトルが同一のニュース。
        - 既に発表済みのツアーやリリースの、単なる続報（リマインド）。
        - 憶測や、公式発表ではない噂レベルの情報。
        - 同一イベントへの出演情報。
        - 表現は異なるが内容が本質的に同一と思われるニュース。

        【回答形式】
        以下の形式を必ず守ってください。

        [SUMMARY]
        (ここにLINE通知用の短文：箇条書き2点以内、各50字以内、URL1つ)
        [DETAIL]
        (ここに保存用の詳細なレポート：ニュースの背景や詳細を含めた丁寧な内容)
        
        差分がほとんど見られない、または前回と同じ内容の場合：
        特になし
        
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        raw_res = response.text.strip()
        
        if "特になし" not in raw_res and "[DETAIL]" in raw_res:
            print(f"✨ {artist}: 新着あり")
            
            try:
                summary_part = raw_res.split("[SUMMARY]")[1].split("[DETAIL]")[0].strip()
                detail_part = raw_res.split("[DETAIL]")[1].strip()
            except:
                summary_part = raw_res[:100]
                detail_part = raw_res

            separator = "\n\n" + "="*30 + "\n\n"
            header = f"📅 {today_display_str} のリサーチ\n"
            updated_content = f"{header}{detail_part}{separator}{old_content}"
            
            with open(new_filename, "w", encoding="utf-8") as f:
                f.write(updated_content.strip())
            
            if old_filename and old_filename != new_filename:
                os.remove(old_filename)

            has_updates_reports.append(f"【{artist}】\n{summary_part}")

        else:
            print(f"✅ {artist}: 変化なし")
            if old_filename and old_filename != new_filename:
                os.rename(old_filename, new_filename)
            no_updates_artists.append(artist)

    message_parts = [f"📢 アーティスト情報 ({today_display_str})\n"]
    if no_updates_artists:
        message_parts.append("■新着なし")
        message_parts.extend(no_updates_artists)
        message_parts.append("")
    if has_updates_reports:
        message_parts.append("■新着あり")
        message_parts.append("\n\n".join(has_updates_reports))

    final_message = "\n".join(message_parts)
    if has_updates_reports or no_updates_artists:
        send_line(final_message)

if __name__ == "__main__":
    search_and_report()