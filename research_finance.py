import os
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_FINANCE_PAGE_ID = os.getenv('NOTION_FINANCE_PAGE_ID')

client = genai.Client(api_key=GEMINI_API_KEY)
FOLDER = "reports_finance"

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
        "parent": { "page_id": NOTION_FINANCE_PAGE_ID }, 
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

def financial_research():
    os.makedirs(FOLDER, exist_ok=True)
    today_dt = datetime.now()
    report_dt = datetime.now() + timedelta(days=1) #UTC22時に実行されるため、1日加算する
    today_display_str = today_dt.strftime('%Y/%m/%d')
    filename_str = report_dt.strftime('%Y_%m_%d')
    
    filename = f"{FOLDER}/finance_report_{filename_str}.txt"

    prompt = f"""
    今日（{today_display_str}）の金融・経済市場について、詳細なリサーチレポートを作成してください。
    
    【【【超重要ルール】】】
    ・「〇〇」や「△△」などの伏せ字、テンプレート形式での回答は【絶対に禁止】です。
    ・必ず検索結果から得られた【具体的な数値（日経平均の終値、ドル円のレート、%など）】を明記してください。
    ・具体的な数値がまだ出ていない場合は、直近（昨晩や数時間前）の確定数値を採用してください。
    
    1⃣以下の項目を網羅し、各項目について専門的な視点で端的に記述してください。
    1. 主要指数の動き（日経平均、NYダウ、S&P500、NASDAQ等）
    2. 為替市場（ドル円、ユーロドル等の動向と要因）
    3. 債券・金利（米10年債利回り等の動き）
    4. 注目ニュース（経済指標の結果、要人発言、個別銘柄の大きな動き）
    5. 今後の展望・リスク要因
    
    2⃣以下の項目について、投資家が【今、最も注目すべき銘柄】を3〜5銘柄厳選し、その根拠をデータドリブンに提示してください。その際、必ず下記の記述フォーマットを厳守してください。
    1. **ボラティリティと出来高**: 単に有名な銘柄ではなく、材料（決算、上方修正、提携、新製品等）により出来高が急増している、または急増が見込まれる銘柄。
    2. **テーマ性**: 半導体、AI、防衛、核融合など、現在の市場テーマのど真ん中にいる銘柄。
    3. **需給とテクニカル**: 年初来高値更新や、移動平均線からの乖離、空売りの買い戻しが期待される状況など。
    
    【各銘柄の記述フォーマット（厳守）】
    ■ [証券コード] 銘柄名
    - **注目理由**: なぜ今日、この銘柄なのか？（決算数値、ニュースの内容を具体的に）
    - **数値データ**: 直近の株価、PER/PBR、時価総額、騰落率を必ず含めること。
    - **投資シナリオ**: 短期的なリバウンド狙いか、中長期のトレンドフォローか。
    - **リスク要因**: どこまで下がったらシナリオ崩壊（損切り）か。
    
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