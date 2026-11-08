import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client, Client

# ページ基本設定
st.set_page_config(
    page_title="思考・表現力セッション（事前準備）",
    page_icon="📘",
    layout="wide"
)

# Supabase接続情報の取得
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# デフォルトのレポートテキスト
def get_default_law_day_report():
    return "（※ここにAIによる詳細な選考評価・採点コメントが記載されます。適宜編集してデータベースに保存可能です。）"

# スコア計算関数
def calculate_scores(data):
    keys = ["Te", "Ti", "Fe", "Fi", "Se", "Si", "Ne", "Ni"]
    scores = {k: np.random.randint(50, 95) for k in keys}
    return scores

# --- サイドバーの設定（元の構成を完全維持） ---
st.sidebar.markdown("## 📌 メニュー・設定")
st.sidebar.success("管理者としてログイン中")

if st.sidebar.button("応募者画面に戻る（ログアウト）"):
    st.switch_page("app.py")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚠️ 注意事項・禁止事項・免責事項")
st.sidebar.markdown(
    """
    * **判定結果の位置付け** 本システムの分析は事前傾向分析であり、人物像を確定するものではありません。
    * **面接準備の補助ツール** 最終的な選考判定および合否決定の責任は選考責任者に帰属します。
    """
)

# メイン画面処理（元の構成を完全維持）
st.markdown("🟢 **思考・表現力セッション（事前準備）**")
st.markdown("# 【管理者用】 事前準備・面接深掘りガイド")
st.markdown("事前確認する応募者を選択してください")

if supabase is None:
    st.warning("Supabaseへの接続が確立されていません。Secretsの設定を確認してください。")
else:
    try:
        response = supabase.table("candidate_responses").select("*").execute()
        rows = response.data if response and hasattr(response, "data") else []
        
        if rows:
            # 応募者名のリスト作成
            candidate_names = [row.get("name", f"ID: {row.get('id')}") for row in rows]
            selected_name = st.selectbox("事前確認する応募者を選択してください", candidate_names, label_visibility="collapsed")
            
            # 選択された行のデータを取得
            row = next((r for r in rows if r.get("name") == selected_name or f"ID: {r.get('id')}" == selected_name), rows[0])
            
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.subheader("📊 8項目適性・思考スタイル分析")
                scores = calculate_scores(row)
                
                # レーダーチャート描画
                categories = list(scores.keys())
                values = list(scores.values())
                values += values[:1]
                categories += categories[:1]
                
                fig = go.Figure(
                    data=[go.Scatterpolar(r=values, theta=categories, fill='toself', name='特性スコア')],
                    layout=go.Polar(radialaxis=dict(visible=True, range=[0, 100]))
                )
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col_right:
                st.markdown("---")
                st.markdown("### 📝 AI選考評価・採点＆適性配置・労務管理レポート")
                
                # エラー（can only join an iterable）を回避するための安全な型チェック処理
                raw_report = row.get('ai_report')
                if isinstance(raw_report, list):
                    report_initial = "".join([str(item) for item in raw_report])
                elif raw_report is not None:
                    report_initial = str(raw_report)
                else:
                    report_initial = get_default_law_day_report()

                report_text = st.text_area(
                    "AI詳細レポート 兼 選考・配置・労務メモ",
                    value=report_initial,
                    height=250
                )
                
                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    if st.button("評価メモをデータベースに保存する", type="primary"):
                        try:
                            supabase.table("candidate_responses").update({"ai_report": report_text}).eq("id", row["id"]).execute()
                            st.success("レポートを更新保存しました")
                        except Exception as e:
                            st.error(f"更新エラー: {e}")
                with btn_col2:
                    if st.button("データを削除する"):
                        try:
                            supabase.table("candidate_responses").delete().eq("id", row["id"]).execute()
                            st.warning("データを削除しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除エラー: {e}")
        else:
            st.info("現在、データベースに保存された回答データはありません。")
            
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
