import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import io
import zipfile
import os

st.set_page_config(page_title="參加證明生成系統", layout="wide")

# 設定中文字型路徑 (請確保資料夾內有此字型檔)
FONT_PATH = "wt064.ttf" #"NotoSansTC-Regular.ttf"

def generate_cert(bg_image, course_name, student_name, date_str, hours_str, y_pos, colors, is_qualified=True):
    """
    根據背景圖片、輸入資訊與排版設定生成證明
    is_qualified=True: 參加證明 (顯示時數)
    is_qualified=False: 完成證明 (不顯示時數，更改內文)
    """
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

    # --- 文字寫入 (套用動態 Y 座標與顏色) ---
    # 課程名稱
    course_text = f"課程名稱：{course_name}"
    _, _, w, h = draw.textbbox((0, 0), course_text, font=font_medium)
    draw.text(((W-w)/2, H * y_pos['course']), course_text, font=font_medium, fill=colors['course'])

    # 茲證明
    certify_text = "茲證明"
    _, _, w, h = draw.textbbox((0, 0), certify_text, font=font_small)
    draw.text(((W-w)/2, H * y_pos['certify']), certify_text, font=font_small, fill=colors['text'])

    # 學員姓名
    _, _, w, h = draw.textbbox((0, 0), student_name, font=font_large)
    draw.text(((W-w)/2, H * y_pos['name']), student_name, font=font_large, fill=colors['name'])

    # 先生/女士
    title_text = "先生/女士"
    _, _, w, h = draw.textbbox((0, 0), title_text, font=font_small)
    draw.text(((W-w)/2, H * y_pos['title']), title_text, font=font_small, fill=colors['text'])

    # 根據資格決定內文與是否顯示時數
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
        
        # 不符合資格者，僅顯示日期，不顯示時數
        _, _, w1, h1 = draw.textbbox((0, 0), date_display, font=font_medium)
        draw.text(((W-w1)/2, H * y_pos['date']), date_display, font=font_medium, fill=colors['date_hours'])

    # 參加/完成 說明內文
    _, _, w, h = draw.textbbox((0, 0), desc_text, font=font_medium)
    draw.text(((W-w)/2, H * y_pos['desc']), desc_text, font=font_medium, fill=colors['text'])

    return img

st.title("🎓 課程證明生成與驗證系統")

# --- 側邊欄：背板設定 ---
st.sidebar.header("🖼️ 1. 背景圖片設定")
bg_option = st.sidebar.radio("選擇背板來源", ["自行上傳背板", "預設背板 1", "預設背板 2", "預設背板 3"])

bg_image = None
if bg_option == "自行上傳背板":
    uploaded_bg = st.sidebar.file_uploader("上傳背板圖片 (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_bg:
        try:
            bg_image = Image.open(uploaded_bg).convert("RGB")
        except UnidentifiedImageError:
            st.sidebar.error("上傳的檔案非有效圖片格式，請重新上傳。")
else:
    bg_dict = {"預設背板 1": "bg1.png", "預設背板 2": "bg2.png", "預設背板 3": "bg3.png"}
    bg_path = bg_dict[bg_option]
    if os.path.exists(bg_path):
        try:
            bg_image = Image.open(bg_path).convert("RGB")
        except UnidentifiedImageError:
            st.sidebar.error(f"檔案 {bg_path} 損毀或格式錯誤。")
    else:
        st.sidebar.warning(f"找不到 {bg_path}。請上傳圖片，或在專案資料夾放入該檔。")

if bg_image is None:
    bg_image = Image.new('RGB', (1600, 1200), color=(255, 255, 255))
    st.sidebar.info("目前使用全白預設背景。")

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

    st.markdown("**上下位置設定 (數值越大越靠下)**")
    y_pos = {
        'course': st.slider("課程名稱 Y 座標", 0.0, 1.0, 0.32, 0.01),
        'certify': st.slider("茲證明 Y 座標", 0.0, 1.0, 0.35, 0.01),
        'name': st.slider("姓名 Y 座標", 0.0, 1.0, 0.38, 0.01),
        'title': st.slider("先生/女士 Y 座標", 0.0, 1.0, 0.42, 0.01),
        'desc': st.slider("參加說明 Y 座標", 0.0, 1.0, 0.47, 0.01),
        'date': st.slider("日期 Y 座標", 0.0, 1.0, 0.56, 0.01),
        'hours': st.slider("時數 Y 座標", 0.0, 1.0, 0.595, 0.01)
    }

# --- 側邊欄：學員驗證資料庫 ---
st.sidebar.header("📂 3. 學員驗證資料庫")
st.sidebar.markdown("請上傳包含 `姓名`, `帳號`, `符合資格` 欄位的 Excel（供自助查詢使用）")
db_file = st.sidebar.file_uploader("上傳學員資料庫", type=["xlsx", "xls"], key="db_upload")

# --- 主畫面：功能分頁 ---
tab1, tab2, tab3 = st.tabs(["📄 單張生成", "📑 Excel 批次生成", "🔍 學員自助查詢與下載"])

# -- 分頁 1：單張生成 --
with tab1:
    st.subheader("個別學員證明生成與預覽")
    col1, col2 = st.columns(2)
    
    with col1:
        default_course = "iPAS 初級AI應用規劃師 重點培訓班"
        course = st.text_input("課程名稱", value=default_course)
        name = st.text_input("學員姓名", value="陳宏銘")
        date_val = st.text_input("上課日期", value="7/6~7/16")
        hours_val = st.text_input("修習時數", value="共8小時")
        cert_type = st.radio("證明類型", ["參加證明 (符合資格, 顯示時數)", "完成證明 (不符合資格, 不顯示時數)"])
        is_qual = True if "參加證明" in cert_type else False
    
    st.markdown("### 👀 即時預覽")
    result_img = generate_cert(bg_image, course, name, date_val, hours_val, y_pos, colors, is_qualified=is_qual)
    st.image(result_img, caption="調整左側面板可即時看到排版變化", use_container_width=True)
    
    buf = io.BytesIO()
    result_img.save(buf, format="PNG")
    st.download_button(
        label="📥 下載此張圖片",
        data=buf.getvalue(),
        file_name=f"{name}_證明.png",
        mime="image/png"
    )

# -- 分頁 2：批次生成 --
with tab2:
    st.subheader("批次生成 (上傳 Excel)")
    st.markdown("請上傳包含 `姓名` 欄位的 Excel。若有 `符合資格` 欄位(填入 Y/N 或 是/否) 系統會自動判斷證明類型。")
    
    col3, col4 = st.columns(2)
    with col3:
        batch_course = st.text_input("統一課程名稱", value="iPAS 初級AI應用規劃師 重點培訓班", key="bc")
        batch_date = st.text_input("統一上課日期", value="7/6~7/16", key="bd")
    with col4:
        batch_hours = st.text_input("統一修習時數", value="共8小時", key="bh")

    uploaded_excel = st.file_uploader("上傳批次名單 Excel", type=["xlsx", "xls"])

    if uploaded_excel:
        df = pd.read_excel(uploaded_excel)
        st.write("預覽資料：", df.head())
        
        if '姓名' not in df.columns:
            st.error("Excel 檔案中找不到「姓名」欄位，請檢查檔案格式！")
        else:
            if st.button("開始批次生成並打包下載", type="primary"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    progress_bar = st.progress(0)
                    total = len(df)
                    
                    for index, row in df.iterrows():
                        s_name = str(row['姓名'])
                        s_course = str(row['課程名稱']) if '課程名稱' in df.columns and pd.notna(row['課程名稱']) else batch_course
                        s_date = str(row['上課日期']) if '上課日期' in df.columns and pd.notna(row['上課日期']) else batch_date
                        s_hours = str(row['修習時數']) if '修習時數' in df.columns and pd.notna(row['修習時數']) else batch_hours
                        
                        # 判斷資格
                        is_qual = True
                        if '符合資格' in df.columns and pd.notna(row['符合資格']):
                            val = str(row['符合資格']).strip().upper()
                            is_qual = val in ['是', 'Y', 'TRUE', '1', 'YES']
                        
                        cert_img = generate_cert(bg_image, s_course, s_name, s_date, s_hours, y_pos, colors, is_qual)
                        
                        img_byte_arr = io.BytesIO()
                        cert_img.save(img_byte_arr, format='PNG')
                        cert_type_str = "參加證明" if is_qual else "完成證明"
                        zip_file.writestr(f"{s_name}_{cert_type_str}.png", img_byte_arr.getvalue())
                        progress_bar.progress((index + 1) / total)
                
                st.success("✅ 批次生成完成！請點擊下方按鈕下載壓縮檔。")
                st.download_button(
                    label="📦 下載全部證明 (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="certificates.zip",
                    mime="application/zip"
                )

# -- 分頁 3：學員自助查詢與下載 --
with tab3:
    st.subheader("🔍 學員自助驗證與下載")
    st.markdown("請輸入您的 **姓名** 與 **帳號** 進行驗證，系統將為您產生對應的證明。")
    
    if db_file is not None:
        try:
            df_db = pd.read_excel(db_file)
            req_cols = ['姓名', '帳號', '符合資格']
            
            # 檢查 Excel 是否包含必要欄位
            if not all(col in df_db.columns for col in req_cols):
                st.error(f"⚠️ 側邊欄上傳的資料庫缺少必要欄位，請確保包含：{', '.join(req_cols)}")
            else:
                col_q1, col_q2 = st.columns(2)
                with col_q1:
                    query_name = st.text_input("請輸入您的姓名")
                with col_q2:
                    query_account = st.text_input("請輸入您的帳號 (如學號或身分證字號)")
                
                if st.button("驗證並查詢", type="primary"):
                    if not query_name or not query_account:
                        st.warning("請填寫姓名與帳號！")
                    else:
                        # 尋找符合的資料
                        # 將帳號都轉為字串比對，避免純數字帳號被當成 int
                        match = df_db[(df_db['姓名'].astype(str) == query_name) & (df_db['帳號'].astype(str) == query_account)]
                        
                        if not match.empty:
                            row = match.iloc[0]
                            # 判斷是否符合資格
                            qual_val = str(row['符合資格']).strip().upper()
                            is_qual = qual_val in ['是', 'Y', 'TRUE', '1', 'YES']
                            
                            s_course = str(row['課程名稱']) if '課程名稱' in df.columns and pd.notna(row['課程名稱']) else default_course
                            s_date = str(row['上課日期']) if '上課日期' in df.columns and pd.notna(row['上課日期']) else "7/6~7/16"
                            s_hours = str(row['修習時數']) if '修習時數' in df.columns and pd.notna(row['修習時數']) else "共8小時"
                            
                            if is_qual:
                                st.success(f"✅ 驗證成功！{query_name} 您符合資格，為您核發「參加證明」。")
                            else:
                                st.info(f"✅ 驗證成功！{query_name} 為您核發「完成證明」。")
                                
                            cert_img = generate_cert(bg_image, s_course, query_name, s_date, s_hours, y_pos, colors, is_qual)
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
                            st.error("❌ 查無資料，請確認您的「姓名」與「帳號」是否輸入正確。")
        except Exception as e:
            st.error(f"讀取資料庫失敗: {e}")
    else:
        st.info("💡 管理員尚未於側邊欄（3. 學員驗證資料庫）上傳學員名單，暫時無法使用查詢功能。")
