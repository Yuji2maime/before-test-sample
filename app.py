import streamlit as st
import google.generativeai as genai

# Streamlitのページ設定
st.set_page_config(page_title="Streamlit - 思考・表現力セッション（事前準備）", layout="wide")

# セッション状態（ログイン状態）の初期化
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# サイドバーの構成（メニュー・設定、管理者ログイン、注意事項）
with st.sidebar:
    st.markdown("### 📌 メニュー・設定")
    st.markdown("#### 🔒 管理者ログイン")
    
    if not st.session_state.is_admin:
        admin_password = st.text_input("パスワードを入力", type="password", key="admin_pass")
        login_btn = st.button("ログイン")
        
        if login_btn:
            if admin_password:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.warning("パスワードを入力してください。")
    else:
        st.success("管理者としてログイン中")
        if st.button("ログアウト"):
            st.session_state.is_admin = False
            st.rerun()

    st.markdown("---")
    st.markdown("#### ⚠️ 注意事項・禁止事項・免責事項")
    st.markdown(
        """
        - **判定結果の位置付け** 本システムの思考性・認知特性分析は、応募者の自己申告テキストに基づく事前傾向分析であり、人物像や能力を確定するものではありません。
        - **面接準備の補助ツール** 本レポートは明日の面接に向けた事前読み込み・質問設計の参考材料です。最終的な選考判定および合否決定、不確定要素の責任は当組織および面接官に帰属します。
        """
    )

# メイン画面のタイトル
st.markdown(
    """
    <div style="background-color: #1E3A8A; padding: 15px; border-radius: 5px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0; color: white;">◆ 思考・表現力セッション（事前準備用）</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# AIレポート生成関数（シビアで適正な評価・コメント抽出）
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

# メイン画面のフォーム構成
st.markdown("## 事前アンケート入力フォーム")

st.markdown(
    """
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #1E3A8A;">【事前提出のご案内】</h4>
        <p style="margin-bottom: 0;">本アンケートは、明日のセッション・面接をより実りあるものにするため、事前に皆様の日常的なお考えや仕事観をお伺いするものです。正解・不正解はございませんので、リラックスしてご自身の率直なお考えをご回答ください。</p>
    </div>
    """,
    unsafe_allow_html=True
)

name = st.text_input("お名前（氏名）", placeholder="例：山田 太郎")
text = st.text_area("思考・表現力に関する記述", placeholder="ご自身の考えや価値観、これまでの経験で大切にしてきたこと等を自由にご記入ください。")

# 提出・レポート生成ボタン
if st.button("事前回答を提出する"):
    if name and text:
        # 管理者としてログインしている場合は、シビアな評価レポート（スコア・コメント）を即座に表示
        if st.session_state.is_admin:
            with st.spinner("AIがレポートを生成中（管理者モード）..."):
                result = generate_gemini_report(name, text)
                st.markdown("---")
                st.markdown("### 📊 【管理者用】AI評価レポート・スコア結果")
                st.markdown(result)
        else:
            with st.spinner("送信中..."):
                st.success("事前回答を受け付けました。ご協力ありがとうございました。")
                st.info("※サイドバーから管理者としてログインすると、AIによるシビアな評価レポート（スコア・コメント・深掘り質問）を確認できます。")
    else:
        st.warning("お名前と記述内容を入力してください。")

# 管理者ログイン中の追加案内
if st.session_state.is_admin:
    st.markdown("---")
    st.info("🔓 現在、**管理者としてログイン中**です。上記のフォームに氏名と記述を入力して「事前回答を提出する」を押すと、シビアな評価レポートやコメントが即座に画面下に表示されます。")
