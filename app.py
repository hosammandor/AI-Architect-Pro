import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, requests, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation
from google.api_core import exceptions

# --- ضبط الترميز للأمان ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="AI Architect Multi-Power", page_icon="🪄", layout="wide")

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

# --- 2. وظائف المساعدة ---
def get_word_download(text):
    doc = Document()
    doc.add_heading('AI Architect Pro - Report', 0)
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

def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. محرك التوليد مع معالجة الموديلات الجديدة ---
def generate_response(provider, api_key, model_name, query, images=None):
    max_retries = 2
    for i in range(max_retries + 1):
        try:
            if provider == "Google Gemini":
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                res = model.generate_content([query] + (images if images else []))
                return res.text
            
            elif provider == "Groq (Ultra Fast)":
                client = Groq(api_key=api_key)
                # فحص تلقائي: إذا كان الطلب فيه صور، نستخدم هيكلية الـ Vision
                if images:
                    msgs = [{
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": query},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(images[0])}"}}
                        ]
                    }]
                else:
                    msgs = [{"role": "user", "content": query}]
                
                res = client.chat.completions.create(messages=msgs, model=model_name)
                return res.choices[0].message.content
        
        except exceptions.ResourceExhausted:
            time.sleep(5); continue
        except Exception as e:
            if "model_decommissioned" in str(e) or "400" in str(e):
                st.error("⚠️ الموديل المختار قديم أو غير مدعوم حالياً. يرجى اختيار موديل آخر من القائمة.")
            else:
                st.error(f"Error: {str(e)}")
            return None
    return None

# --- 4. القائمة الجانبية (تحديث موديلات Groq لعام 2026) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    provider = st.selectbox("AI Provider:", ["Google Gemini", "Groq (Ultra Fast)"])
    api_key = st.text_input(f"{provider} API Key:", type="password")
    
    if api_key:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            models = [m.name.replace('models/', '') for l in [genai.list_models()] for m in l if 'generateContent' in m.supported_generation_methods]
            model_choice = st.selectbox("Model:", models, index=0)
        else:
            # الموديلات المحدثة لـ Groq بعد إيقاف النسخ القديمة
            model_choice = st.selectbox("Model:", [
                "llama-3.3-70b-versatile",    # الأقوى للنصوص والجداول
                "llama-3.2-11b-vision-preview", # جرب هذا للرؤية إذا كان متاحاً
                "llama-3.1-8b-instant",        # فائق السرعة
                "mixtral-8x7b-32768"           # بديل مستقر جداً
            ])
            st.warning("ملاحظة: موديلات Vision في Groq تتغير باستمرار. إذا فشل التحليل، جرب موديل Gemini.")

# --- 5. واجهة المستخدم ---
if api_key:
    st.markdown("<h1 style='text-align: center;'>🪄 AI Architect <span style='color: #00d2ff;'>Multi-Power</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["✨ Image Prompts", "📸 Vision Studio", "📑 Ultimate Doc Analyzer", "🧠 Universal Architect"])

    # (نفس منطق التابات السابقة مع تحسين الربط)
    with tabs[2]:
        docs = st.file_uploader("Files (PDF, Word, Excel, PPT, Code, Text)", type=["pdf", "docx", "xlsx", "pptx", "txt", "py", "jpg", "png"], accept_multiple_files=True)
        payload_text = []
        payload_imgs = []
        if docs:
            for d in docs[:10]:
                ext = d.name.split('.')[-1].lower()
                if ext in ['docx', 'xlsx', 'pptx']: payload_text.append(process_office_file(d))
                elif ext in ['txt', 'py']: payload_text.append(f"File: {d.name}\n{d.getvalue().decode('utf-8')}")
                elif ext == 'pdf':
                    pdf = fitz.open(stream=d.read(), filetype="pdf")
                    for p in pdf: payload_imgs.append(Image.open(io.BytesIO(p.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                elif ext in ['jpg', 'png', 'jpeg']: payload_imgs.append(Image.open(d))
            st.success(f"Loaded {len(docs[:10])} files.")

        d_q = st.text_area("Instructions:")
        if st.button("Deep Analysis 🚀"):
            full_context = "\n".join(payload_text) + "\n\n" + d_q
            res = generate_response(provider, api_key, model_choice, full_context, payload_imgs if payload_imgs else None)
            if res: 
                st.session_state['doc_res'] = res
                st.code(res, language="markdown")
                c1, c2 = st.columns(2)
                c1.download_button("Word 📄", get_word_download(res), "Report.docx")
                ex = get_excel_download(res)
                if ex: c2.download_button("Excel 📊", ex, "Data.xlsx")

    # (بقية التابات كما هي في النسخة السابقة)
    with tabs[0]:
        p_q = st.text_area("Image Idea:")
        if st.button("Build"):
            r = generate_response(provider, api_key, model_choice, f"Pro prompt for: {p_q}")
            if r: st.code(r)
else:
    st.info("👈 Please select a provider and enter API Key.")
