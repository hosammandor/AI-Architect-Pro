import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time
import requests
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation
from google.api_core import exceptions

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="AI Architect Pro", page_icon="🪄", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%); color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; color: white; font-weight: bold; }
    .stButton>button { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); color: white; border: none; padding: 12px; border-radius: 12px; font-weight: 700; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0px 10px 20px rgba(0, 210, 255, 0.3); }
    .result-box { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; border-left: 5px solid #00d2ff; margin-top: 15px; }
    section[data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.8); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظيفة المعالجة الآمنة (حل مشكلة Quota) ---
def safe_generate_content(model, payload):
    max_retries = 3
    for i in range(max_retries):
        try:
            return model.generate_content(payload)
        except exceptions.ResourceExhausted:
            if i < max_retries - 1:
                wait_time = (i + 1) * 5
                st.warning(f"⚠️ الحصة ممتلئة.. سأحاول مرة أخرى تلقائياً خلال {wait_time} ثواني...")
                time.sleep(wait_time)
            else:
                st.error("❌ تم تجاوز حصة الاستخدام المجانية لليوم. يرجى اختيار موديل Flash أو المحاولة لاحقاً.")
        except Exception as e:
            st.error(f"❌ حدث خطأ: {e}")
            break
    return None

# --- 3. وظائف تصدير وتحليل الملفات ---
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

def process_office_file(file):
    ext = file.name.split('.')[-1].lower()
    content = ""
    try:
        if ext == 'docx':
            doc = Document(file)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'pptx':
            prs = Presentation(file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): content += shape.text + "\n"
        elif ext == 'xlsx':
            df = pd.read_excel(file)
            content = "Excel Summary:\n" + df.to_string()
    except Exception as e: content = f"Error reading file: {e}"
    return f"--- File: {file.name} ---\n{content}"

# --- 4. القائمة الجانبية ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key:", type="password")
    current_model = "gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            current_model = st.selectbox("Intelligence Level:", [m for m in available_models if "1.5" in m] or available_models, index=0)
            st.info("💡 نصيحة: موديل Flash حصته أكبر وأقل عرضة لخطأ Quota.")
        except: st.error("Invalid API Key")

# --- 5. واجهة المستخدم الرئيسية ---
if api_key:
    try:
        model = genai.GenerativeModel(current_model)
        st.markdown("<h1 style='text-align: center;'>🪄 AI <span style='color: #00d2ff;'>Architect</span> Pro</h1>", unsafe_allow_html=True)
        
        tabs = st.tabs(["✨ Image Prompts", "📸 Vision Studio", "📑 Ultimate Doc Analyzer", "🧠 Universal Architect"])

        # --- Ultimate Doc Analyzer (القسم الأكثر تطوراً) ---
        with tabs[2]:
            st.markdown("### 📑 PDF, Office, Code & Text Intelligence")
            allowed_types = ["pdf", "png", "jpg", "txt", "py", "docx", "xlsx", "pptx"]
            up_docs = st.file_uploader("ارفع حتى 10 ملفات متنوعة", type=allowed_types, accept_multiple_files=True)
            
            final_payload = []
            if up_docs:
                for doc in up_docs[:10]:
                    ext = doc.name.split('.')[-1].lower()
                    if ext in ['docx', 'xlsx', 'pptx', 'txt', 'py']:
                        final_payload.append(process_office_file(doc) if ext in ['docx', 'xlsx', 'pptx'] else f"File: {doc.name}\n{doc.getvalue().decode('utf-8')}")
                    elif ext == "pdf":
                        pdf_file = fitz.open(stream=doc.read(), filetype="pdf")
                        for page in pdf_file:
                            pix = page.get_pixmap(matrix=fitz.Matrix(1,1)) # جودة متوسطة لتوفير الحصة
                            final_payload.append(Image.open(io.BytesIO(pix.tobytes("png"))))
                    else:
                        final_payload.append(Image.open(doc))
                st.success(f"تم تجهيز {len(up_docs[:10])} ملفات.")

            d_query = st.text_area("التعليمات:", placeholder="لخص الملفات، استخرج جداول، أو قارن البيانات...")
            
            if st.button("Deep Analysis 🚀") and final_payload:
                with st.spinner("🧠 جاري التحليل مع حماية الحصة (Safe Processing)..."):
                    res = safe_generate_content(model, [d_query] + final_payload)
                    if res: st.session_state['final_res'] = res.text
                    
            if 'final_res' in st.session_state:
                st.markdown("### 🔍 نتائج التحليل:")
                st.code(st.session_state['final_res'], language="markdown") # ميزة النسخ المباشر
                
                st.markdown("### 📥 تحميل وتصدير:")
                c1, c2 = st.columns(2)
                c1.download_button("Download Report (Word) 📄", get_word_download(st.session_state['final_res']), "AI_Insight.docx")
                ex = get_excel_download(st.session_state['final_res'])
                if ex: c2.download_button("Download Data (Excel) 📊", ex, "Extracted_Data.xlsx")

        # التابات الأخرى مع استخدام Safe Generate
        with tabs[0]:
            st.markdown("### ✍️ Image Prompts Builder")
            raw_p = st.text_area("Describe idea:", key="t0_p")
            if st.button("Build Prompt"):
                r = safe_generate_content(model, f"Pro prompt for {raw_p}")
                if r: st.code(r.text)

        with tabs[1]:
            st.markdown("### 📸 Vision Intelligence")
            v_ups = st.file_uploader("Images", type=["jpg", "png"], key="t1_up", accept_multiple_files=True)
            if v_ups:
                q_v = st.text_input("Question?")
                if st.button("Analyze"):
                    r = safe_generate_content(model, [q_v] + [Image.open(f) for f in v_ups])
                    if r: st.markdown(f'<div class="result-box">{r.text}</div>', unsafe_allow_html=True)

        with tabs[3]:
            st.markdown("### 🧠 Universal Prompt Architect")
            u_in = st.text_area("Request Idea:", key="t3_in")
            if st.button("Generate Professional Prompt"):
                r = safe_generate_content(model, f"Professional structured prompt for: {u_in}")
                if r: st.code(r.text)

    except Exception as e: st.error(f"General Error: {e}")
else:
    st.info("👈 يرجى إدخال API Key للبدء")
