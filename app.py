import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go

# 1. ページ基本設定
st.set_page_config(
    page_title="思考・表現力セッション（事前準備）- 労働調査会",
    page_icon="🔹",
    layout="wide"
)

# カスタムCSS（ブルー系テーマ）
st.markdown("""
<style>
    .day-banner {
        background-color: #1E3A8A;
        color: #FFFFFF !important;
        padding: 10px 18px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 20px;
    }
    .day-title {
        color: #1E3A8A;
        border-bottom: 3px solid #1E3A8A;
        padding-bottom: 6px;
        margin-bottom: 15px;
        font-size: 1.6rem;
        font-weight: bold;
    }
    .instruction-box {
        background-color: #f0f4f8;
        color: #1e293b !important;
        border-left: 5px solid #1E3A8A;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    .instruction-box h4 {
        color: #1E3A8A !important;
        margin-top: 0;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .instruction-box p {
        color: #1e293b !important;
        margin-bottom: 0;
    }
    div.stButton > button:first-child {
        background-color: #2563EB;
        color: white !important;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        padding: 8px 16px;
    }
    div.stButton > button:first-child:hover {
        background-color: #1E3A8A;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="day-banner">🔹 思考・表現力セッション（事前準備用）</div>', unsafe_allow_html=True)

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Supabase接続エラー: {e}")

gemini_ready = False
if "GEMINI_API_KEY" in st.secrets:
    try:
        raw_key = str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
        genai.configure(api_key=raw_key)
        gemini_ready = True
    except Exception:
        gemini_ready = False

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

def analyze_text_simple(text):
    judging = "Te型（効率・構造化）" if any(w in text for w in ["効率", "計画", "目標", "構造", "成果", "システム"]) else \
              "Ti型（論理・分析）" if any(w in text for w in ["論理", "分析", "仕組み", "本質", "理由"]) else \
              "Fe型（調和・配慮）" if any(w in text for w in ["調和", "チーム", "協力", "感謝", "配慮"]) else \
              "Fi型（価値観・内省）"
    
    perceiving = "Se（現場・実行）" if any(w in text for w in ["行動", "現場", "実践", "体験", "スピード"]) else \
                 "Si（経験・確実）" if any(w in text for w in ["経験", "規則", "確実", "継続", "積み重ね"]) else \
                 "Ne（アイデア・可能性）" if any(w in text for w in ["発想", "アイデア", "挑戦", "可能性", "変化"]) else \
                 "Ni（本質・洞察）"
                 
    return [judging, f"補助{perceiving}"]

def calculate_scores(text, types_list):
    types_str = " ".join(types_list)
    base = 55 + (len(text) % 15)
    
    scores = {
        "Te": base + 15 if "Te" in types_str or any(w in text for w in ["効率", "目標", "計画"]) else base - 10,
        "Ti": base + 10 if "Ti" in types_str or any(w in text for w in ["論理", "分析", "仕組み"]) else base - 5,
        "Fe": base + 10 if "Fe" in types_str or any(w in text for w in ["調和", "協力", "感謝"]) else base - 10,
        "Fi": base + 15 if "Fi" in types_str or any(w in text for w in ["価値観", "想い", "寄り添"]) else base - 5,
        "Se": base + 10 if "Se" in types_str or any(w in text for w in ["行動", "現場", "実践"]) else base - 10,
        "Si": base + 10 if "Si" in types_str or any(w in text for w in ["経験", "規則", "確実"]) else base - 10,
        "Ne": base + 10 if "Ne" in types_str or any(w in text for w in ["発想", "挑戦", "変化"]) else base - 10,
        "Ni": base + 10 if "Ni" in types_str or any(w in text for w in ["洞察", "未来", "ビジョン"]) else base - 10,
    }
    for k in scores:
        scores[k] = max(35, min(95, scores[k]))
    return scores

def generate_gemini_report(name, text):
    bad_keywords = ["セックス", "オナニー", "ブルマー", "スケベ", "暴れ", "死ね", "殺す", "風俗"]
    if any(k in text for k in bad_keywords):
        return (
            "【AI面接前日準備・質問設計ガイド】\n"
            "■ 思考傾向・テキストの評価:\n"
            "■ 【 ⚠️ 重大警告・不採用推奨】公序良俗に反する表現および就労目的から著しく逸脱した記述が含まれています。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・ 社会的適合性および就労意欲の根幹に著しい欠如が見られます。\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:"
        )
    elif len(text) < 30:
        return (
            "【AI面接前日準備・質問設計ガイド】\n"
            "■ 思考傾向・テキストの評価: 記述内容が非常に簡素であり、自己の考えや思考プロセスの具体性が不足しています。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・ 口頭での説明能力や具体性を交えた回答ができるかを確認してください。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「記述いただいた内容について、具体的な実体験やエピソードを詳しく教えていただけますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:"
        )

    def generate_gemini_report(name, text):
    bad_keywords = ["セックス", "オナニー", "ブルマー", "スケベ", "暴れ", "死ね", "殺す", "風俗"]
    if any(k in text for k in bad_keywords):
        return (
            "【AI面接前日準備・質問設計ガイド】\n"
            "■ 思考傾向・テキストの評価: 【重大警告・即不採用推奨】公序良俗に著しく反し、社会人としての適性が完全に欠落しています。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・就労意識、倫理観、コンプライアンス意識のすべてにおいて致命的な問題があります。採用は絶対に避けてください。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「このような記述を行った意図は何ですか？ご自身の発言の重大さを理解していますか？」\n"
            "■ 面接事前準備メモ (面接官の事前メモ欄) :\n"
            "即時不採用。面接の時間を割く価値もありません。"
        )
    
    prompt = f"""あなたは企業採用および労務管理における極めて厳格かつ鋭敏な人事選考・認知心理の専門アナリストです。
以下の応募者の自己申告テキストを容赦なく分析し、面接官が事前に把握すべき「極めてシビアかつ辛口な評価レポート」を【必ずすべて日本語】で作成してください。

応募者氏名: {name}
記述内容: {text}

【厳格な評価ルール】
1. 甘い評価、無理なポジティブ化、お世辞は一切禁止です。少しでも不適切な動機、幼稚さ、協調性の欠如、モラルハザードの兆候があれば、徹底的に突いてください。
2. 記述内容が不真面目、倫理的に問題がある、または能力・意欲に著しい懸念がある場合は、忖度なく「0点」レベルの評価を下し、即不採用を推奨する警告を出力してください。
3. 良い点が見当たらなければ、無理に良い点を作らず「注意点・リスク・欠陥」のみをストレートに指摘してください。
4. 面接官が当日、本人の化けの皮を剥がすために「どう厳しく追及すべきか」の具体的な深掘り質問を必ず提示してください。

以下の見出しを使って、必ずすべて日本語でレポートを作成してください。

【AI面接前日準備・質問設計ガイド】
■ 思考傾向・テキストの評価:
■ 明日の面接での着眼点・観察ポイント:
■ 明日使える深掘り質問例:
■ 面接事前準備メモ (面接官の事前メモ欄) :
"""

    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                try:
                    model = genai.GenerativeModel(m.name)
                    response = model.generate_content(
                        prompt,
                        generation_config={"temperature": 0.1}
                    )
                    if response and hasattr(response, 'text') and response.text:
                        res_text = response.text
                        return res_text
                except Exception:
                    continue
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
    return "APIからの応答を取得できませんでした。"
