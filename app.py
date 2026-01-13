import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os
import requests
import fitz  # PyMuPDF
import pandas as pd
from docx import Document

# --- 1. إعدادات الصفحة والتصميم العصري (Glassmorphism) ---
st.set_page_config(page_title="AI Architect Pro", page_icon="🪄", layout="wide")

st.markdown("""
    <style>
    /* الخلفية والتنسيق العام */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%); color: #ffffff; }
    
    /* تنسيق التابات */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: rgba(255, 255, 255, 0.05); 
        border-radius: 10px; color: white; font-weight: bold; font-size: 14px;
    }

    /* تحسين الأزرار */
    .stButton>button { 
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); 
        color: white; border: none; padding: 12px; border-radius: 12px; 
        font-weight: 700; width: 100%; transition: 0.3s; 
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0px 10px 20px rgba(0, 210, 255, 0.3); }

    /* صناديق النتائج */
    .result-box { 
        background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px; border-left: 5px solid #00d2ff; 
        margin-top: 15px; line-height: 1.6; 
    }

    /* القائمة الجانبية */
    section[data-testid="stSidebar"] { 
        background-color: rgba(15, 23, 42, 0.8); border-right: 1px solid rgba(255, 255, 255, 0.1); 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف تصدير الملفات (Word & Excel) ---
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

# --- 3. القائمة الجانبية وإدارة الـ API ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key:", type="password")
    current_model = "gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            current_model = st.selectbox("Intelligence Level:", [m for m in available_models if "1.5" in m] or available_models)
        except: st.error("Invalid API Key or Connection Issue")

# --- 4. واجهة المستخدم والتابات ---
if api_key:
    try:
        model = genai.GenerativeModel(current_model)
        st.markdown("<h1 style='text-align: center;'>🪄 AI <span style='color: #00d2ff;'>Architect</span> Pro</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["✨ Image Prompts", "📸 Vision Studio", "📑 Multi-Doc Analyzer", "🧠 Universal Architect"])

        # --- Tab 1: مهندس برومبتات الصور ---
        with tab1:
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("### ✍️ Image Concept")
                raw_img = st.text_area("وصف الصورة المطلوبة:", placeholder="مثلاً: محارب قديم بأسلوب السايبربانك في شوارع القاهرة...", height=150)
                target = st.selectbox("Target AI Platform:", ["Midjourney v6", "DALL-E 3", "Leonardo AI"])
                if st.button("Optimize Prompt 🎨"):
                    if raw_img:
                        res = model.generate_content(f"Convert this idea into a high-detail English image prompt for {target}: {raw_img}")
                        st.session_state['img_p'] = res.text
            with col2:
                if 'img_p' in st.session_state:
                    st.markdown("### 🚀 Resulting Prompt")
                    st.code(st.session_state['img_p'])
                    st.balloons()

        # --- Tab 2: استوديو الرؤية (صور متعددة وروابط) ---
        with tab2:
            st.markdown("### 👁️ Vision Intelligence")
            v_mode = st.radio("Source Mode:", ["Upload Images", "Image URL"], horizontal=True)
            v_items = []
            if v_mode == "Upload Images":
                ups = st.file_uploader("ارفع حتى 10 صور", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
                if ups:
                    for f in ups[:10]: v_items.append(Image.open(f))
                    st.success(f"Loaded {len(v_items)} images.")
            else:
                url = st.text_input("Paste Image URL:")
                if url:
                    r = requests.get(url); v_items.append(Image.open(io.BytesIO(r.content))); st.image(v_items[0], width=300)

            v_query = st.text_input("ماذا تريد أن تعرف عن هذه الصور؟")
            if st.button("Analyze 🔍") and v_items:
                with st.spinner("Thinking..."):
                    res = model.generate_content([v_query if v_query else "Describe these images"] + v_items)
                    st.markdown(f'<div class="result-box">{res.text}</div>', unsafe_allow_html=True)

        # --- Tab 3: محلل الملفات المتقدم (Up to 10 Files) ---
        with tab3:
            st.markdown("### 📑 PDF, Code, Text & Data Intelligence")
            docs = st.file_uploader("ارفع ملفاتك (PDF, Image, TXT, PY) - بحد أقصى 10", type=["pdf", "png", "jpg", "txt", "py"], accept_multiple_files=True)
            
            final_payload = []
            if docs:
                for doc in docs[:10]:
                    ext = doc.name.split('.')[-1].lower()
                    if ext in ['txt', 'py']:
                        final_payload.append(f"File Name: {doc.name}\nContent:\n{doc.getvalue().decode('utf-8')}")
                    elif ext == "pdf":
                        pdf_file = fitz.open(stream=doc.read(), filetype="pdf")
                        for page in pdf_file:
                            pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5))
                            final_payload.append(Image.open(io.BytesIO(pix.tobytes("png"))))
                    else:
                        final_payload.append(Image.open(doc))
                st.success(f"Ready to analyze {len(docs[:10])} files.")

            d_query = st.text_area("التعليمات:", placeholder="قارن، لخص، أو استخرج جداول البيانات...")
            if st.button("Execute Multi-Analysis 🚀") and final_payload:
                with st.spinner("Processing all files..."):
                    res = model.generate_content([d_query] + final_payload)
                    st.session_state['d_res'] = res.text
                    st.markdown(f'<div class="result-box">{res.text}</div>', unsafe_allow_html=True)
                
            if 'd_res' in st.session_state:
                st.markdown("### 📥 Download Results")
                c1, c2 = st.columns(2)
                c1.download_button("Word Document 📄", get_word_download(st.session_state['d_res']), "AI_Report.docx")
                ex_file = get_excel_download(st.session_state['d_res'])
                if ex_file: c2.download_button("Excel Sheet 📊", ex_file, "Data_Extract.xlsx")

        # --- Tab 4: مهندس الأوامر الشامل ---
        with tab4:
            st.markdown("### 🧠 Universal Prompt Architect")
            ca, cb = st.columns(2, gap="large")
            with ca:
                u_input = st.text_area("فكرتك لأي مجال (برمجة، تسويق، كتابة):", placeholder="أريد خطة عمل لمطعم صحي...", height=150)
                if st.button("Build Professional Prompt 🔨"):
                    if u_input:
                        sys_prompt = "Act as an Expert Prompt Engineer. Assignments: Role, Context, Task, Constraints, and Output Format. Generate in English."
                        res = model.generate_content(f"{sys_prompt}\n\nUser Idea: {u_input}")
                        st.session_state['u_p'] = res.text
            with cb:
                if 'u_p' in st.session_state:
                    st.markdown("### 📋 Engineered Prompt")
                    st.code(st.session_state['u_p'], language="text")

    except Exception as e: st.error(f"Error occurred: {e}")
else:
    st.markdown("<div style='text-align: center; padding: 100px; color: #94a3b8;'><h2>👋 يرجى إدخال API Key للبدء</h2><p>يمكنك الحصول عليه من Google AI Studio</p></div>", unsafe_allow_html=True)
