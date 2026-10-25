import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go

# 1. ページ基本設定（事前準備）
st.set_page_config(
    page_title="思考・表現力セッション",
    page_icon="🟢",
    layout="wide"
)

# カスタムCSS（統一されたクリーンなデザイン）
st.markdown("""
<style>
    .day-banner {
        background-color: #0F766E;
        color: #FFFFFF !important;
        padding: 10px 18px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 20px;
    }
    .day-title {
        color: #0F766E;
        border-bottom: 3px solid #0F766E;
        padding-bottom: 6px;
        margin-bottom: 15px;
        font-size: 1.6rem;
        font-weight: bold;
    }
    .instruction-box {
        background-color: #f8f9fa;
        color: #212529 !important;
        border-left: 5px solid #0F766E;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    .instruction-box h4 {
        color: #0F766E !important;
        margin-top: 0;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .instruction-box p {
        color: #212529 !important;
        margin-bottom: 0;
    }
    div.stButton > button:first-child {
        background-color: #0F766E;
        color: white !important;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        padding: 8px 16px;
    }
    div.stButton > button:first-child:hover {
        background-color: #115e59;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="day-banner">🟢 思考・表現力セッション（労働調査会用・事前準備）</div>', unsafe_allow_html=True)

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
# 補助関数（全4アプリ共通のシンプル・頑健ロジック）
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
    risk_keywords = ["違反", "不正", "力こそが正義", "馬鹿", "軍人", "SEX", "オナニー", "ブルマー", "いびっ"]
    has_risk = any(k in text for k in risk_keywords)
    
    if len(text) < 30 or has_risk:
        base = 20
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
    
    if len(text) < 30 or has_risk:
        for k in scores:
            scores[k] = min(scores[k], 25)
            
    for k in scores:
        scores[k] = max(10, min(95, scores[k]))
    return scores

def get_default_before_law_report(text):
    risk_keywords = ["違反", "不正", "力こそが正義", "馬鹿", "軍人", "SEX", "オナニー", "ブルマー", "いびっ"]
    if any(k in text for k in risk_keywords):
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 特になし\n"
            "・短所・リスク・懸念点: 【🚨 重大コンプライアンスリスク】組織の規範遵守を軽視する傾向が示されており、面接において厳格な確認が必要です。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・社会的規範意識、倫理観、および組織のルールに対する基本的態度を厳格に見極める。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「組織のルールやコンプライアンスに関するお考えについて具体的にご説明いただけますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・コンプライアンス上の重大なリスクがあるため面接にて厳しく追及すること。"
        )
    elif len(text) < 30:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 簡潔に意向を示そうとする姿勢。\n"
            "・短所・リスク・懸念点: 【🚨 記述量・論理的説明の不足（慎重評価）】記述量が極めて少なく、具体的な行動根拠や論理性が欠如している点。表面的な言葉にとどまるリスク。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・抽象的な表現の裏にある具体的な行動実績と論理的思考力を面接口頭で見極める。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「ご自身の主張を裏付ける具体的なエピソードや、過去に直面した課題とその解決策を教えてください。」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・表層的な表現に終始しているため、面接にて実践力と論理性を厳しく追及すること。"
        )
    else:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 自身の考えや価値観を一定の言葉で表現できている点。\n"
            "・短所・リスク・懸念点: 理想論や主観に偏る傾向が見られる場合があり、実際の業務における客観的判断力の検証が必要な点。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・主観的な意欲だけでなく、客観的な状況判断力と組織への適応バランスが取れているかを確認する。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「ご自身の意見や価値観と、組織の方針やチームのルールが異なる場合、どのように折り合いをつけて行動しますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・面接にて客観的思考力とプレッシャーへの耐性、ガバナンス意識を重点的に確認すること。"
        )

# ----------------------------------------------------
# サイドバー
# ----------------------------------------------------
st.sidebar.title("📌 メニュー・設定")

if not st.session_state.is_admin:
    st.sidebar.subheader("🔒 管理者ログイン")
    password_input = st.sidebar.text_input("パスワードを入力", type="password")
    if st.sidebar.button("ログイン"):
        if password_input == "8888":  # 労働調査会用パスワード
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
  本システムの分析は事前傾向分析であり、人物像を確定するものではありません。
- **面接準備の補助ツール**
  最終的な選考判定および合否決定の責任は選考責任者に帰属します。
""")

# ----------------------------------------------------
# A. 応募者入力画面
# ----------------------------------------------------
if not st.session_state.is_admin:
    st.markdown('<h1 class="day-title">事前アンケート入力フォーム</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="instruction-box">
        <h4 style="margin-top: 0; color: #0F766E;">【事前提出のご案内】</h4>
        <p style="margin-bottom: 0;">本アンケートは、明日のセッション・面接をより実りあるものにするため、事前に皆様の日常的なお考えや仕事観をお伺いするものです。正解・不正解はございませんので、リラックスしてご自身の率直なお考えをご回答ください。</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key="candidate_form_before_law"):
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
# B. 管理者画面（ai_memo_before_law カラムを使用）
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
                        fillcolor='rgba(15, 118, 110, 0.4)',
                        line=dict(color='#0F766E', width=2)
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False,
                        margin=dict(l=40, r=40, t=30, b=30),
                        height=380
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")
                st.markdown("### 📝 AI面接前日準備・質問設計ガイド")
                
                saved_memo = selected_candidate.get("ai_memo_before_law", "")
                
                if not saved_memo or "選考評価＆配属活用レポート" in str(saved_memo):
                    default_memo = get_default_before_law_report(candidate_text.strip())
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
