import os
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_TECH_PAGE_ID = os.getenv('NOTION_TECH_PAGE_ID')

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
        "parent": { "page_id": NOTION_TECH_PAGE_ID }, 
        "properties": {
            "title": [{"text": {"content": title}}]
        },
        "children": blocks
    }
    
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ ページ '{title}' を作成しました。")
    else:
        print(f"❌ Notionエラー: {response.text}")

def tech_research():
    today_dt = datetime.now()
    today_display_str = today_dt.strftime('%Y/%m/%d')
    filename_str = today_dt.strftime('%Y_%m_%d')
    
    filename = f"Tech_Report_{filename_str}.txt"
    
    prompt = f"""
    今日（{today_display_str}）の最新テクノロジーニュースをGoogle検索で調査し、プロフェッショナルなリサーチレポートを作成してください。
    
    【【【絶対厳守】】】
    ・「〇〇」や「今後の動向が注目されます」といった中身のない表現は【禁止】です。
    ・具体的な【製品名】【モデル名】【企業名】【ベンチマーク数値】【発表された仕様】を必ず含めてください。
    ・特に AI（LLM）、最新ガジェット（Apple/Nvidia/OpenAI等）、半導体、Web技術に焦点を当ててください。

    レポート構成：
    1. 本日の最重要テックトピック（1〜2件を深く解説）
    2. AI・ソフトウェア開発動向（最新の論文やアップデート）
    3. ハードウェア・ガジェット情報（新製品やリーク情報）
    4. 注目すべきテック企業の株価やビジネス動向
    5. 技術的な要点まとめ

    1行目をタイトル（例：2026/03/02 テック概況 - OpenAIの新型モデル発表など）とし、2行目以降を本文にしてください。
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
    title = lines[0] if lines else f"テックリサーチ {today_display_str}"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_report)
    print(f"📄 ファイル保存完了: {filename}")
    
    create_notion_page(title, full_report)

if __name__ == "__main__":
    tech_research()