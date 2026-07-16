import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import io
import os

st.set_page_config(page_title="學員證明自助查詢系統", layout="wide")

# ==========================================
# 🛑 從 Streamlit Secrets 讀取隱藏的資料庫連結
# ==========================================
if "DB_URL" in st.secrets:
    GOOGLE_SHEET_CSV_URL = st.secrets["DB_URL"]
else:
    GOOGLE_SHEET_CSV_URL = None

# 設定中文字型路徑 (請確保資料夾內有此字型檔)
FONT_PATH = "wt064.ttf" #"NotoSansTC-Regular.ttf"
# ==========================================

def generate_cert(bg_image, course_name, student_name, date_str, hours_str, y_pos, colors, is_qualified=True):
    img = bg_image.copy()
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype(FONT_PATH, 60)
        font_medium = ImageFont.truetype(FONT_PATH, 48)
        font_small = ImageFont.truetype(FONT_PATH, 36)
    except IOError:
        st.error(f"找不到字型檔 {FONT_PATH}，請確認檔案是否存在！")
        return img

    W, H = img.size

    course_text = f"課程名稱：{course_name}"
    _, _, w, h = draw.textbbox((0, 0), course_text, font=font_medium)
    draw.text(((W-w)/2, H * y_pos['course']), course_text, font=font_medium, fill=colors['course'])

    certify_text = "茲證明"
    _, _, w, h = draw.textbbox((0, 0), certify_text, font=font_small)
    draw.text(((W-w)/2, H * y_pos['certify']), certify_text, font=font_small, fill=colors['text'])

    _, _, w, h = draw.textbbox((0, 0), student_name, font=font_large)
    draw.text(((W-w)/2, H * y_pos['name']), student_name, font=font_large, fill=colors['name'])

    title_text = "先生/女士"
    _, _, w, h = draw.textbbox((0, 0), title_text, font=font_small)
    draw.text(((W-w)/2, H * y_pos['title']), title_text, font=font_small, fill=colors['text'])

    if is_qualified:
        desc_text = "參加上述課程並完成學習，特發此參加證明以資證明。"
        date_display = f"上課日期：{date_str}"
        hours_display = f"修習時數：{hours_str}"
        
        _, _, w1, h1 = draw.textbbox((0, 0), date_display, font=font_medium)
        _, _, w2, h2 = draw.textbbox((0, 0), hours_display, font=font_medium)
        
        draw.text(((W-w1)/2, H * y_pos['date']), date_display, font=font_medium, fill=colors['date_hours'])
        draw.text(((W-w2)/2, H * y_pos['hours']), hours_display, font=font_medium, fill=colors['date_hours'])
    else:
        desc_text = "完成上述課程學習，特發此完成證明以資鼓勵。"
        date_display = f"上課日期：{date_str}"
        
        _, _, w1, h1 = draw.textbbox((0, 0), date_display, font=font_medium)
        draw.text(((W-w1)/2, H * y_pos['date']), date_display, font=font_medium, fill=colors['date_hours'])

    _, _, w, h = draw.textbbox((0, 0), desc_text, font=font_medium)
    draw.text(((W-w)/2, H * y_pos['desc']), desc_text, font=font_medium, fill=colors['text'])

    return img

# 輔助函式：載入背景圖片 (優先使用上傳的圖片，否則抓預設路徑，最後用白底)
def load_background(uploaded_file, default_path):
    if uploaded_file:
        try:
            return Image.open(uploaded_file).convert("RGB")
        except UnidentifiedImageError:
            st.sidebar.error("上傳的檔案非有效圖片格式。")
    if os.path.exists(default_path):
        try:
            return Image.open(default_path).convert("RGB")
        except UnidentifiedImageError:
            st.sidebar.error(f"檔案 {default_path} 損毀或格式錯誤。")
    
    # 防呆機制：如果都沒有，給一張全白背景
    return Image.new('RGB', (1600, 1200), color=(255, 255, 255))

st.title("🎓 課程證明自助查詢與下載系統")

# --- 側邊欄：雙背板設定 ---
st.sidebar.header("🖼️ 1. 背景圖片設定")
st.sidebar.markdown("""
系統已預設：
- 符合資格 ➔ 使用 `bg1.png`
- 不符合資格 ➔ 使用 `bg2.png`

*(若需臨時更換，可於下方上傳覆蓋預設)*
""")

bg1_upload = st.sidebar.file_uploader("上傳「參加證明」背板", type=["png", "jpg", "jpeg"], key="bg1")
bg2_upload = st.sidebar.file_uploader("上傳「完成證明」背板", type=["png", "jpg", "jpeg"], key="bg2")

# 取得最終要使用的兩張背板
bg1_image = load_background(bg1_upload, "bg1.png")
bg2_image = load_background(bg2_upload, "bg2.png")

# 檢查檔案是否遺失，提醒管理員
if not bg1_upload and not os.path.exists("bg1.png"):
    st.sidebar.warning("找不到 bg1.png，符合資格者將顯示全白背景。")
if not bg2_upload and not os.path.exists("bg2.png"):
    st.sidebar.warning("找不到 bg2.png，不符合資格者將顯示全白背景。")


# --- 側邊欄：排版與顏色微調 ---
st.sidebar.header("✍️ 2. 文字排版與顏色微調")
with st.sidebar.expander("展開微調面板 (調整座標與顏色)", expanded=False):
    st.markdown("**顏色設定**")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        color_course = st.color_picker("課程名稱顏色", "#502814")
        color_name = st.color_picker("姓名顏色", "#501414")
    with col_c2:
        color_text = st.color_picker("一般內文顏色", "#000000")
        color_date_hours = st.color_picker("日期時數顏色", "#323232")
    
    colors = {
        'course': color_course, 'name': color_name, 
        'text': color_text, 'date_hours': color_date_hours
    }

    st.markdown("**上下位置設定**")
    y_pos = {
        'course': st.slider("課程名稱 Y 座標", 0.0, 1.0, 0.32, 0.01),
        'certify': st.slider("茲證明 Y 座標", 0.0, 1.0, 0.35, 0.01),
        'name': st.slider("姓名 Y 座標", 0.0, 1.0, 0.38, 0.01),
        'title': st.slider("先生/女士 Y 座標", 0.0, 1.0, 0.42, 0.01),
        'desc': st.slider("參加說明 Y 座標", 0.0, 1.0, 0.47, 0.01),
        'date': st.slider("日期 Y 座標", 0.0, 1.0, 0.56, 0.01),
        'hours': st.slider("時數 Y 座標", 0.0, 1.0, 0.595, 0.01)
    }

# --- 主畫面：學員自助查詢與下載 ---
st.subheader("🔍 學員自助驗證與下載")
st.markdown("請輸入您的 **姓名** 與 **帳號** 進行驗證，系統將為您產生對應的證明。")

if GOOGLE_SHEET_CSV_URL:
    try:
        df_db = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        req_cols = ['姓名', '帳號', '符合資格']
        
        if not all(col in df_db.columns for col in req_cols):
            st.error(f"⚠️ 系統錯誤：後台資料庫缺少必要欄位 ({', '.join(req_cols)})，請聯繫管理員。")
        else:
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                query_name = st.text_input("請輸入您的姓名")
            with col_q2:
                query_account = st.text_input("請輸入您的帳號 (如學號或身分證字號)", type="password")
            
            if st.button("驗證並查詢", type="primary"):
                if not query_name or not query_account:
                    st.warning("請填寫姓名與帳號！")
                else:
                    match = df_db[(df_db['姓名'].astype(str) == query_name) & (df_db['帳號'].astype(str) == query_account)]
                    
                    if not match.empty:
                        row = match.iloc[-1]
                        
                        qual_val = str(row['符合資格']).strip().upper()
                        is_qual = qual_val in ['是', 'Y', 'TRUE', '1', 'YES']
                        
                        s_course = str(row['課程名稱']) if '課程名稱' in df_db.columns and pd.notna(row['課程名稱']) else "iPAS 初級AI應用規劃師 重點培訓班"
                        s_date = str(row['上課日期']) if '上課日期' in df_db.columns and pd.notna(row['上課日期']) else "7/6~7/16"
                        s_hours = str(row['修習時數']) if '修習時數' in df_db.columns and pd.notna(row['修習時數']) else "共8小時"
                        
                        # 核心變更：根據資格選擇要傳入的背板圖片
                        selected_bg = bg1_image if is_qual else bg2_image
                        
                        if is_qual:
                            st.success(f"✅ 驗證成功！{query_name} 您符合資格，為您核發「參加證明」。")
                        else:
                            st.info(f"✅ 驗證成功！{query_name} 為您核發「完成證明」。")
                            
                        # 使用動態選擇的 selected_bg 來生成證明
                        cert_img = generate_cert(selected_bg, s_course, query_name, s_date, s_hours, y_pos, colors, is_qual)
                        st.image(cert_img, use_container_width=True)
                        
                        buf = io.BytesIO()
                        cert_img.save(buf, format="PNG")
                        cert_type_str = "參加證明" if is_qual else "完成證明"
                        st.download_button(
                            label="📥 下載您的證明",
                            data=buf.getvalue(),
                            file_name=f"{query_name}_{cert_type_str}.png",
                            mime="image/png"
                        )
                    else:
                        st.error("❌ 查無資料，請確認您的「姓名」與「帳號」是否輸入正確，或聯繫管理員確認報名狀態。")
    except Exception as e:
        st.error("系統維護中：無法讀取後台資料庫，請稍後再試或聯繫管理員。")
else:
    st.warning("⚠️ 系統尚未設定資料庫，無法使用查詢功能。(管理員請於後台設定 Secrets 變數 DB_URL)")
