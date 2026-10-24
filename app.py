import streamlit as st
import google.generativeai as genai

# Streamlitのページ設定
st.set_page_config(page_title="思考・表現力セッション（事前準備用）", layout="wide")

st.markdown(
    """
    <div style="background-color: #1E3A8A; padding: 15px; border-radius: 5px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0; color: white;">◆ 思考・表現力セッション（事前準備用）</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# 入力フォームの作成
name = st.text_input("応募者氏名")
text = st.text_area("応募者の事前アンケート記述内容")

def generate_gemini_report(name, text):
    prompt = f"""
あなたは採用面接の専門家です。
※出力は、コード内の見出し等を除き、解説や分析コメントなどは必ずすべて「日本語」で行ってください（英語の使用は厳禁です）。
以下の応募者の事前アンケート記述内容を評価・分析し、面接官が前日に確認するための「事前準備レポート」を作成してください。

【応募者氏名】: {name}
【記述内容】:
"{text}"

【出力フォーマット（必ずこの形式で出力してください）】:
【AI面接事前準備レポート（深掘り質問ガイド）】
■ 思考傾向・テキストの評価:
（回答の具体性、論理性、就労意欲、公序良俗・倫理感の観点から評価。不適切な記述や著しい意欲の欠如が見られる場合は、その旨と重大な懸念・選考見送り推奨を明確に述べること。）

【評価・指導方針】
1. 思考傾向・テキストの評価においては、表面的な言葉遣いだけでなく、記述から読み取れる応募者の価値観、課題解決アプローチ、ならびに組織に対する姿勢を深く洞察して分析してください。
2. 記述内容が不真面目、倫理的に問題がある、または能力・意欲に著しい懸念がある場合は、忖度なく「0点」レベルの評価を下し、即不採用を推奨する警告を出力してください。
3. 良い点が見当たらなければ、無理に良い点を作らず「注意点・リスク・欠陥」のみをストレートに指摘してください。
4. 面接官が当日、本人の化けの皮を剥がすために「どう厳しく追及すべきか」の具体的な深掘り質問を必ず提示してください。

以下の見出しを使って、必ずすべて日本語でレポートを作成してください。


【AI面接前日準備・質問設計ガイド】
■ 思考傾向・テキストの評価:
■ 明日の面接での着眼点・観察ポイント:
■ 明日使える深掘り質問例:
■ 面接事前準備メモ（面接官の事前メモ欄）:
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

# 実行ボタン
if st.button("レポート生成"):
    if name and text:
        with st.spinner("AIがレポートを生成中..."):
            result = generate_gemini_report(name, text)
            st.markdown(result)
    else:
        st.warning("応募者氏名と記述内容を入力してください。")
