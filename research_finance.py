import os
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_PARENT_PAGE_ID = os.getenv('NOTION_PARENT_PAGE_ID')

client = genai.Client(api_key=GEMINI_API_KEY)

def create_notion_page(title, full_text):
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    blocks = []
    for line in full_text.split("\n"):
        if line.strip():
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": line}}]}
            })

    data = {
        "parent": { "page_id": PARENT_PAGE_ID }, 
        "properties": {
            "title": [{"text": {"content": title}}]
        },
        "children": blocks
    }
    
    print(f"📡 Notionへ送信中... 親ページID: {PARENT_PAGE_ID}")
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ 成功！ページ '{title}' を作成しました。")
    else:
        print(f"❌ Notionエラー: {response.text}")

def financial_research():
    print("--- 総合金融リサーチ開始 ---")
    today_dt = datetime.now()
    today_display_str = today_dt.strftime('%Y/%m/%d')
    filename_str = today_dt.strftime('%Y_%m_%d')
    
    filename = f"finance_report_{filename_str}.txt"

    prompt = f"""
    今日（{today_display_str}）の金融・経済市場について、詳細なリサーチレポートを作成してください。
    
    以下の項目を網羅し、各項目について専門的な視点で詳しく記述してください。
    1. 主要指数の動き（日経平均、NYダウ、S&P500、NASDAQ等）
    2. 為替市場（ドル円、ユーロドル等の動向と要因）
    3. 債券・金利（米10年債利回り等の動き）
    4. 注目ニュース（経済指標の結果、要人発言、個別銘柄の大きな動き）
    5. 今後の展望・リスク要因
    
    【回答形式】
    1行目：レポートのタイトル（例：2026/03/02 金融市場概況 - 〇〇の上昇と円安の背景）
    2行目以降：上記項目に沿った詳細な本文（マークダウン形式で読みやすく）
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    full_report = response.text.strip()
    
    lines = full_report.split("\n")
    title = lines[0] if lines else f"金融リサーチ {today_display_str}"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_report)
    print(f"📄 ファイル保存完了: {filename}")

    create_notion_page(title, full_report)

if __name__ == "__main__":
    financial_research()