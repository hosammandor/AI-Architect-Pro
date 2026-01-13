import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os
import requests
import fitz  # PyMuPDF
import pandas as pd
from docx import Document

# --- 1. إعدادات الصفحة والتصميم العصري ---
st.set_page_config(page_title="AI Architect Pro", page_icon="🪄", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%); color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; color: white; font-weight: bold; }
    .stButton>button { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); color: white; border: none; padding: 12px; border-radius: 12px; font-weight: 700; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0px 10px 20px rgba(0, 210, 255, 0.3); }
    .result-box { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 15px; border-left: 5px solid #00d2ff; margin-top: 15px; line-height: 1.6; }
    section[data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.8); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف التصدير (Word & Excel) ---
def get_word_download(text):
    doc = Document()
    doc.add_heading('AI Architect Pro - Analysis Report', 0)
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def get_excel_download(text):
    try:
        from io import StringIO
        if "|" in text:
            lines = [l.strip() for l in text.split('\n') if "|" in l]
            if len(lines) > 2:
                df = pd.read_csv(StringIO('\n'.join(lines)), sep="|", skipinitialspace=True).dropna(axis=1, how='all')
                df.columns = [c.strip() for c in df.columns]
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                return out.getvalue()
    except: return None
    return None

# --- 3. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key:", type="password")
    current_model = "gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            current_model = st.selectbox("Intelligence Level:", available_models, index=0)
        except: st.error("Invalid API Key")

# --- 4. المحتوى الرئيسي ---
if api_key:
    try:
        model = genai.GenerativeModel(current_model)
        st.markdown("<h1 style='text-align: center;'>🪄 AI <span style='color: #00d2ff;'>Architect</span> Pro</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["✨ Image Prompts", "📸 Vision Studio", "📑 Doc Intelligence", "🧠 Universal Architect"])

        # --- Tab 1: مهندس برومبتات الصور ---
        with tab1:
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("### ✍️ Image Vision")
                raw_img_input = st.text_area("صف فكرتك:", placeholder="مثلاً: قصر طائر فوق السحاب بأسلوب مستقبلي...", height=150)
                target_platform = st.selectbox("Target AI:", ["Midjourney v6", "DALL-E 3", "Leonardo AI"])
                if st.button("Generate Image Prompt 🎨"):
                    if raw_img_input:
                        with st.spinner("Engineering..."):
                            res = model.generate_content(f"Act as a professional image prompt engineer. Create a high-quality English prompt for {target_platform} based on: {raw_img_input}")
                            st.session_state['img_p_res'] = res.text
            with col2:
                if 'img_p_res' in st.session_state:
                    st.markdown("### 🚀 Optimized Prompt")
                    st.code(st.session_state['img_p_res'])
                    st.balloons()

        # --- Tab 2: استوديو الرؤية والروابط ---
        with tab2:
            st.markdown("### 👁️ Analyze Images & URLs")
            v_mode = st.radio("Source:", ["Upload", "URL"], horizontal=True)
            v_imgs = []
            if v_mode == "Upload":
                up_v = st.file_uploader("Image", type=["png", "jpg", "jpeg"], key="v_up")
                if up_v: v_imgs.append(Image.open(up_v)); st.image(v_imgs[0], width=300)
            else:
                u_url = st.text_input("Image URL:")
                if u_url:
                    try:
                        r = requests.get(u_url, timeout=10)
                        v_imgs.append(Image.open(io.BytesIO(r.content))); st.image(v_imgs[0], width=300)
                    except: st.error("رابط غير صحيح")
            
            v_q = st.text_input("ماذا تريد من الذكاء الاصطناعي؟ (مثلاً: حلل، ترجم، أو عدل)")
            if st.button("Analyze 🔍") and v_imgs:
                with st.spinner("Analyzing..."):
                    res = model.generate_content([v_q if v_q else "Describe this image", v_imgs[0]])
                    st.markdown(f'<div class="result-box">{res.text}</div>', unsafe_allow_html=True)

        # --- Tab 3: ذكاء المستندات والتحويل ---
        with tab3:
            st.markdown("### 📑 PDF & Data Extraction")
            up_doc = st.file_uploader("PDF/Scanned Doc", type=["pdf", "png", "jpg"])
            doc_imgs = []
            if up_doc:
                if up_doc.type == "application/pdf":
                    pdf = fitz.open(stream=up_doc.read(), filetype="pdf")
                    for page in pdf:
                        pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
                        doc_imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))))
                else: doc_imgs.append(Image.open(up_doc))
            
            doc_q = st.text_area("تعليمات الاستخراج:", placeholder="استخرج الجداول المالية، لخص المحتوى، أو حوله لنص...")
            if st.button("Extract Data 🚀") and doc_imgs:
                with st.spinner("Processing Document..."):
                    res = model.generate_content([doc_q] + doc_imgs)
                    st.session_state['doc_res'] = res.text
                    st.markdown(f'<div class="result-box">{res.text}</div>', unsafe_allow_html=True)
                
            if 'doc_res' in st.session_state:
                c1, c2 = st.columns(2)
                c1.download_button("Download Word 📄", get_word_download(st.session_state['doc_res']), "Report.docx")
                ex = get_excel_download(st.session_state['doc_res'])
                if ex: c2.download_button("Download Excel 📊", ex, "Data_Extract.xlsx")

        # --- Tab 4: مهندس الأوامر الشامل ---
        with tab4:
            st.markdown("### 🧠 Universal Prompt Architect")
            col_a, col_b = st.columns(2, gap="large")
            with col_a:
                general_input = st.text_area("ما هي المهمة التي تريد بناء أمر لها؟", placeholder="مثلاً: أريد كتابة مقال عن الفضاء، أو كود برمجي لتطبيق موبايل...", height=150)
                if st.button("Build Professional Prompt 🔨"):
                    if general_input:
                        with st.spinner("Architecting..."):
                            sys_instr = "Act as an Expert Prompt Engineer. Assign a Role, Context, Task, and Output Format. Generate in English."
                            response = model.generate_content(f"{sys_instr}\n\nTask Idea: {general_input}")
                            st.session_state['univ_p'] = response.text
            with col_b:
                if 'univ_p' in st.session_state:
                    st.markdown("### 📋 الأمر الهندسي الجاهز")
                    st.code(st.session_state['univ_p'], language="text")
                    st.success("انسخ هذا الأمر واستخدمه في أي شات للحصول على نتائج احترافية!")

    except Exception as e: st.error(f"Error: {e}")
else:
    st.markdown("<div style='text-align: center; padding: 100px;'><h2>👋 مرحباً بك! يرجى إدخال مفتاح الـ API للبدء</h2></div>", unsafe_allow_html=True)
