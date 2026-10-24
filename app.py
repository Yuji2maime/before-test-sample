import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go

# 1. ページ基本設定
st.set_page_config(
    page_title="Streamlit - 思考・表現力セッション（事前準備）",
    page_icon="🔵",
    layout="wide"
)

# カスタムCSS（落ち着いたブルー系）
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

# ヘッダーバナー
st.markdown('<div class="day-banner">◆ 思考・表現力セッション（事前準備用）</div>', unsafe_allow_html=True)

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

# セッション状態の初期化
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ----------------------------------------------------
# 補助関数：タイプ判定とスコア計算
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

# Gemini安全生成関数（純粋な日本語のみ・長所と短所を織り交ぜたシビアな分析）
def generate_gemini_report_day(name, text):
    prompt = f"""以下の応募者の事前アンケート記述内容を分析し、面接官向けの詳細な事前準備レポートをすべて日本語で作成してください。英語やシステム指示の混入は一切禁止します。

【応募者氏名】: {name}
【記述内容】:
"{text}"

以下の見出し構成に従い、長所と短所を織り交ぜてシビアかつ深く掘り下げた分析を行ってください。

【AI面接事前準備レポート（深掘り質問ガイド）】
■ 思考傾向・テキストの評価（長所と短所分析）:
・長所・評価できる点: （記述から読み取れる意欲や強み）
・短所・リスク・懸念点: （具体性の欠如や懸念されるリスク）

■ 明日の面接での着眼点・観察ポイント:
（面接官が注目すべき観察点）

■ 明日使える深掘り質問例:
1. （本質や事実を確認するための質問）
2. （懸念点や矛盾を突くための厳格な質問）

■ 面接事前準備メモ（面接官の事前メモ欄）:
（選考上の総合的な警戒レベルや申し送り事項）"""

    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        for model_name in available_models:
            try:
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt, generation_config={"temperature": 0.1})
                if res and hasattr(res, 'text') and res.text:
                    if any(eng in res.text for eng in ["Applicant", "Goal", "Constraints", "Role:", "Description:"]):
                        continue
                    return res.text
            except Exception:
                continue
    except Exception:
        pass

    # フォールバックエンジン（完全日本語・長所短所シビア評価）
    bad_keywords = ["セックス", "オナニー", "ブルマー", "スケベ", "暴れ", "死ね", "殺す", "風俗"]
    if any(k in text for k in bad_keywords):
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: なし\n"
            "・短所・リスク・懸念点: 【重大な不採用推奨】公序良俗に反する表現および就労目的から著しく逸脱した記述が含まれています。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・組織のコンプライアンス維持の観点から選考見送りを強く推奨します。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「ご自身の記述された内容について、社会的マナーや倫理観の観点からどのように説明されますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・コンプライアンス上の重大なリスクがあるため採用不可。"
        )
    elif len(text) < 30:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 相手に配慮しようとする意向が見られる点。\n"
            "・短所・リスク・懸念点: 記述が極めて短く抽象的であり、具体的にどのような行動をとるのか根拠が欠如している点。口先だけの理想論に終わるリスクがある。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・「寄り添う」という言葉の裏にある具体的行動力や精神的耐性を口頭で見極める。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「『患者に寄り添う』とは、具体的にどのような行動を指すと考えていますか？過去の実践例を教えてください。」\n"
            "2. 「自分の親身な対応が相手に受け入れられなかったり、理不尽に拒絶された場合、どのように対応しますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・表層的な表現に終始しているため、面接にて実践力と論理性を厳しく追及すること。"
        )
    else:
        return (
            "【AI面接事前準備レポート（深掘り質問ガイド）】\n"
            "■ 思考傾向・テキストの評価（長所と短所分析）:\n"
            "・長所・評価できる点: 他者への共感性や対人配慮の意向が強く伺える点。\n"
            "・短所・リスク・懸念点: 感情面への配慮に偏るあまり、客観的判断や業務効率を重視すべき場面での判断力に課題が残る点。\n"
            "■ 明日の面接での着眼点・観察ポイント:\n"
            "・共感性とプロ意識（毅然とした対応）のバランスが取れているかを確認する。\n"
            "■ 明日使える深掘り質問例:\n"
            "1. 「相手の感情に共感することと、プロとして冷静に客観的判断を下すことのバランスをどのように取りますか？」\n"
            "2. 「ご自身の価値観と組織のルールが対立した際、どちらを優先して行動しますか？」\n"
            "■ 面接事前準備メモ（面接官の事前メモ欄）:\n"
            "・面接にて客観的思考力とプレッシャーへの耐性を厳しく確認すること。"
        )

# ----------------------------------------------------
# サイドバー：メニュー、管理者ログイン/ログアウト、免責事項
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
# A. 応募者入力画面（未ログイン時）
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
# B. 管理者画面（ログイン時：事前準備・面接深掘りガイド）
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
                # AI面接前日準備・質問設計ガイド
                # ----------------------------------------------------
                st.markdown("---")
                st.markdown("### 📝 AI面接前日準備・質問設計ガイド")
                
                saved_memo = selected_candidate.get("ai_memo", "")
                
                # 保存されているデータに英語が含まれている場合は即座に破棄して日本語で再生成
                is_invalid_english = any(eng in str(saved_memo) for eng in ["Applicant", "Goal", "Constraints", "Role:", "Description:", "Content:"])
                
                if not saved_memo or is_invalid_english:
                    with st.spinner("記述内容を分析し、完全な日本語レポートを作成中..."):
                        default_memo = generate_gemini_report_day(selected_candidate.get('name'), candidate_text.strip())
                        try:
                            supabase.table("candidate_responses").update({"ai_memo": default_memo}).eq("id", record_id).execute()
                        except Exception:
                            pass
                else:
                    default_memo = saved_memo

                memo_input = st.text_area("AI面接事前準備メモ（面接官の事前メモ欄）", value=default_memo, height=260)
                
                btn_c1, btn_c2 = st.columns([1, 1])
                
                with btn_c1:
                    if st.button("💾 事前メモをデータベースに保存する"):
                        try:
                            supabase.table("candidate_responses").update({"ai_memo": memo_input}).eq("id", record_id).execute()
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
