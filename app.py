import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go

# 1. ページ基本設定
st.set_page_config(
    page_title="思考・表現力セッション（労働調査会用・事前準備）",
    page_icon="🔵",
    layout="wide"
)

# カスタムCSS
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
        background-color: #F8FAFC;
        color: #212529 !important;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 5px;
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
        color: #212529 !important;
        margin-bottom: 0;
    }
    div.stButton > button:first-child {
        background-color: #1E3A8A;
        color: white !important;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        padding: 8px 16px;
    }
    div.stButton > button:first-child:hover {
        background-color: #1d4ed8;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="day-banner">◆ 思考・表現力セッション（労働調査会用・事前準備）</div>', unsafe_allow_html=True)

# Supabase初期化
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Supabase接続エラー: {e}")

# Gemini API初期化
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

# ----------------------------------------------------
# 補助関数
# ----------------------------------------------------
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
    bad_keywords = ["セックス", "オナニー", "ブルマー", "スケベ", "暴れ", "死ね", "殺す", "風俗"]
    if any(k in text for k in bad_keywords) or len(text) < 15:
        base = 25
    else:
        base = 45 + (len(text) % 25)
    
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
        scores[k] = max(10, min(95, scores[k]))
    return scores

# 記述内容に応じた個別最適化テンプレート（前日用）
def get_default_before_report(text):
    bad_keywords = ["セックス", "オナニー", "ブルマー", "スケベ", "暴れ", "死ね", "殺す", "風俗"]
    if any(k in text for k in bad_keywords):
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: なし\n"
            "・短所・リスク・懸念点: 【重大な不採用推奨】公序良俗に反する表現および就労目的から著しく逸脱した記述が含まれています。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・組織のコンプライアンス維持の観点から面接での厳格な確認を推奨します。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「ご自身の記述された内容について、社会的マナーや倫理観の観点から面接官にどのように説明されますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・コンプライアンス上の重大なリスクがあるため面接にて厳しく追及すること。"
        )
    elif "営業" in text or "オンナ" in text or "女" in text:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 営業職に対する意欲や欲望に直結した強いハングリー精神。\n"
            "・短所・リスク・懸念点: 動機が極めて不適切かつ表層的であり、コンプライアンス意識や倫理観に重大な欠陥が疑われる点。顧客トラブルを引き起こすリスクが極めて高い。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・営業職としての正当な目的意識、倫理規範の有無、顧客や他者に対する誠実性を厳格に見極める。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「営業職で成果を上げるために、どのような行動や倫理観が必要だと考えていますか？」\n"
            "2. 「自分の成果や目的のためであれば、組織のルールやマナーを逸脱してもよいと考えますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・動機の健全性とコンプライアンス意識に重大な懸念あり。面接にて厳しい追及が必要。"
        )
    elif "看護師" in text or "患者" in text or "寄り添" in text:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 患者や弱者に対する強い共感性と寄り添いの姿勢。\n"
            "・短所・リスク・懸念点: 感情的な寄り添いに偏るあまり、客観的な医療判断や厳しい現場環境下でのストレス耐性に課題が生じる可能性。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・「寄り添う」という言葉の裏にある具体的な行動力、プロとしての冷静な判断力および精神的耐性を見極める。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「『患者に寄り添う』とは具体的にどのような対応を指すとお考えですか？過去の実践例を教えてください。」\n"
            "2. 「自身の親身な対応が拒絶されたり、理不尽な事態に直面した際、冷静さをどう保ちますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・共感性は良好。面接にて実践的な判断力とストレス耐性を重点的に確認すること。"
        )
    else:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 独自の視点や意欲が見られる点。\n"
            "・短所・リスク・懸念点: 記述が短く具体性に欠けるため、行動根拠や論理性の検証が必要な点。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・抽象的な表現にとどまらない具体的な行動実績と達成意欲を見極める。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「記述いただいた内容について、具体的なエピソードや根拠を詳しく教えてください。」\n"
            "2. 「直面した課題に対して、ご自身でどのように論理的に解決してきましたか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・面接にて具体的な行動プロセスと論理的思考力を確認すること。"
        )

# ----------------------------------------------------
# サイドバー
# ----------------------------------------------------
st.sidebar.title("📌 メニュー・設定")

if not st.session_state.is_admin:
    st.sidebar.subheader("🔒 管理者ログイン")
    password_input = st.sidebar.text_input("パスワードを入力", type="password")
    if st.sidebar.button("ログイン"):
        if password_input == "LawC8001":
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.sidebar.error("パスワードが違います")
else:
    st.sidebar.success("管理者としてログイン中")
    if st.sidebar.button("🔄 応募者画面へ戻る（ログアウト）"):
        st.session_state.is_admin = False
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("⚠️ 注意事項・禁止事項・免責事項")
st.sidebar.info("""
- **判定結果の位置付け**
  本システムの思考性・認知特性分析は、応募者の自己申告テキストに基づく事前傾向分析であり、人物像や能力を確定するものではありません。
- **面接準備の補助ツール**
  本レポートは明日の面接に向けた事前読み込み・質問設計の参考材料です。**最終的な選考判定および合否決定、不確定要素の責任は当組織および面接官に帰属します。**
- **個人情報の管理・禁止事項**
  採用選考以外の目的での使用、および第三者への無断漏洩・共有は厳禁です。
""")

# ----------------------------------------------------
# A. 応募者入力画面
# ----------------------------------------------------
if not st.session_state.is_admin:
    st.markdown('<h1 class="day-title">事前アンケート入力フォーム</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="instruction-box">
        <h4 style="margin-top: 0; color: #1E3A8A;">【事前提出のご案内】</h4>
        <p style="margin-bottom: 0;">本アンケートは、明日のセッション・面接をより実りあるものにするため、事前に皆様の日常的なお考えや仕事観をお伺いするものです。正解・不正解はございませんので、リラックスしてご自身の率直なお考えをご回答ください。</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key="candidate_form_day"):
        applicant_name = st.text_input("お名前（氏名）", placeholder="例：山田 太郎")
        applicant_text = st.text_area("思考・表現力に関する記述", height=150, placeholder="ご自身の考えや価値観、これまでの経験で大切にしてきたこと等を自由にご記入ください。")
        
        submit_button = st.form_submit_button(label="事前回答を提出する")

    if submit_button:
        if not applicant_name.strip() or not applicant_text.strip():
            st.warning("お名前と記述内容の両方を入力してください。")
        else:
            try:
                types_val = analyze_text_simple(applicant_text.strip())
                new_data = {
                    "name": applicant_name.strip(),
                    "text": applicant_text.strip(),
                    "types": types_val,
                    "app_type": "day"
                }
                supabase.table("candidate_responses").insert(new_data).execute()
                st.success("事前回答を受け付けました。ご協力ありがとうございました。")
            except Exception as e:
                st.error(f"送信時にエラーが発生しました: {e}")

# ----------------------------------------------------
# B. 管理者画面
# ----------------------------------------------------
else:
    st.markdown('<h1 class="day-title">【管理者用】事前準備・面接深掘りガイド</h1>', unsafe_allow_html=True)
    
    try:
        response = supabase.table("candidate_responses").select("*").execute()
        data = response.data
        
        if data:
            names = [item.get("name", "無名") for item in data]
            selected_name = st.selectbox("事前確認する応募者を選択してください", names)
            selected_candidate = next((item for item in data if item.get("name") == selected_name), None)
            
            if selected_candidate:
                record_id = selected_candidate.get("id")
                candidate_text = selected_candidate.get("text", "")
                candidate_types = selected_candidate.get("types", [])
                
                scores_dict = calculate_scores(candidate_text, candidate_types)

                col_left, col_right = st.columns([1.1, 1])
                
                with col_left:
                    st.markdown(f"### 👤 応募者氏名: **{selected_candidate.get('name')}**")
                    st.markdown("#### 【事前記述内容】")
                    st.info(candidate_text if candidate_text else "記述内容がありません。")
                    
                    st.markdown("#### 【判定タイプ & 認知特性スコア】")
                    st.write(f"判定タイプ / 認知特性: `{candidate_types}`")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Te (効率)", f"{scores_dict['Te']}点")
                    c2.metric("Ti (論理)", f"{scores_dict['Ti']}点")
                    c3.metric("Fe (調和)", f"{scores_dict['Fe']}点")
                    c4.metric("Fi (内省)", f"{scores_dict['Fi']}点")
                    
                    c1.metric("Se (実行)", f"{scores_dict['Se']}点")
                    c2.metric("Si (確実)", f"{scores_dict['Si']}点")
                    c3.metric("Ne (発想)", f"{scores_dict['Ne']}点")
                    c4.metric("Ni (洞察)", f"{scores_dict['Ni']}点")

                with col_right:
                    st.markdown("#### 【思考・認知特性レーダーチャート】")
                    categories = ['Te', 'Ti', 'Fe', 'Fi', 'Se', 'Si', 'Ne', 'Ni']
                    values = [scores_dict[k] for k in categories]
                    fig = go.Figure(data=go.Scatterpolar(
                        r=values + [values[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        fillcolor='rgba(30, 58, 138, 0.4)',
                        line=dict(color='#1E3A8A', width=2)
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False,
                        margin=dict(l=40, r=40, t=30, b=30),
                        height=380
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # ----------------------------------------------------
                # レポート表示（記述キーワードから自動切り替え）
                # ----------------------------------------------------
                st.markdown("---")
                st.markdown("### 📝 AI面接前日準備・質問設計ガイド")
                
                saved_memo = selected_candidate.get("ai_memo_before_law", "")
                
                # 既存データが古い汎用文面の場合もキーワード分岐で上書き生成
                if not saved_memo or "選考評価＆配属活用レポート" in str(saved_memo) or "患者に寄り添う" in str(saved_memo) and "営業" in candidate_text:
                    default_memo = get_default_before_report(candidate_text.strip())
                    try:
                        supabase.table("candidate_responses").update({"ai_memo_before_law": default_memo}).eq("id", record_id).execute()
                    except Exception:
                        pass
                else:
                    default_memo = saved_memo

                memo_input = st.text_area("AI面接事前準備メモ（面接官の事前メモ欄）", value=default_memo, height=260)
                
                btn_c1, btn_c2 = st.columns([1, 1])
                
                with btn_c1:
                    if st.button("💾 事前メモをデータベースに保存する"):
                        try:
                            supabase.table("candidate_responses").update({"ai_memo_before_law": memo_input}).eq("id", record_id).execute()
                            st.success("事前メモを保存しました。")
                        except Exception as e:
                            st.error(f"保存エラー: {e}")

                with btn_c2:
                    if st.button("🗑️ データを削除する"):
                        try:
                            supabase.table("candidate_responses").delete().eq("id", record_id).execute()
                            st.success("データを削除しました。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除エラー: {e}")

        else:
            st.info("登録されている応募者データがありません。")
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
