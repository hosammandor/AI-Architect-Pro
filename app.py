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

# --- 3. محرك التوليد الآمن (تعديل الموديلات) ---
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
                # التحقق مما إذا كان الموديل يدعم الرؤية (Vision)
                if images and ("vision" in model_name.lower() or "90b" in model_name.lower()):
                    msgs = [{"role": "user", "content": [{"type": "text", "text": query}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(images[0])}"}}]}]
                else:
                    msgs = [{"role": "user", "content": query}]
                res = client.chat.completions.create(messages=msgs, model=model_name)
                return res.choices[0].message.content
        
        except exceptions.ResourceExhausted:
            if i < max_retries: time.sleep(5); continue
            else: st.error("Quota Exceeded!"); return None
        except Exception as e:
            st.error(f"Error: {str(e)}"); return None
    return None

# --- 4. القائمة الجانبية (تحديث الموديلات هنا) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    provider = st.selectbox("AI Provider:", ["Google Gemini", "Groq (Ultra Fast)"])
    api_key = st.text_input(f"{provider} API Key:", type="password")
    
    if api_key:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_choice = st.selectbox("Model:", models, index=0)
        else:
            # تم تحديث الموديلات هنا لتجنب خطأ الـ Decommissioned
            model_choice = st.selectbox("Model:", [
                "llama-3.3-70b-versatile",    # الأحدث والأقوى للنصوص
                "llama-3.2-90b-vision-preview", # الموديل البديل للرؤية (Vision)
                "llama-3.1-8b-instant",        # فائق السرعة
                "mixtral-8x7b-32768"           # موديل بديل ممتاز
            ])

# --- 5. واجهة المستخدم ---
if api_key:
    st.markdown("<h1 style='text-align: center;'>🪄 AI Architect <span style='color: #00d2ff;'>Multi-Power</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["✨ Image Prompts", "📸 Vision Studio", "📑 Ultimate Doc Analyzer", "🧠 Universal Architect"])

    # --- Tab 1: Image Prompts ---
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            raw_p = st.text_area("وصف الصورة:", placeholder="مثلاً: بطل خارق بزي فرعوني...")
            target = st.selectbox("Target:", ["Midjourney", "DALL-E 3", "Leonardo AI"])
            if st.button("Build Image Prompt"):
                res = generate_response(provider, api_key, model_choice, f"Pro prompt for {target}: {raw_p}")
                if res: st.session_state['img_res'] = res
        with col2:
            if 'img_res' in st.session_state:
                st.code(st.session_state['img_res'])

    # --- Tab 2: Vision Studio ---
    with tabs[1]:
        v_ups = st.file_uploader("Upload Images (Up to 10)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        v_q = st.text_input("What to do with images?")
        if st.button("Analyze Vision"):
            imgs = [Image.open(f) for f in v_ups] if v_ups else []
            res = generate_response(provider, api_key, model_choice, v_q if v_q else "Describe these", imgs)
            if res: st.markdown(f'<div class="result-box">{res}</div>', unsafe_allow_html=True)

    # --- Tab 3: Ultimate Doc Analyzer ---
    with tabs[2]:
        docs = st.file_uploader("Files (PDF, Word, Excel, PPT, Code, Text)", type=["pdf", "docx", "xlsx", "pptx", "txt", "py", "jpg", "png"], accept_multiple_files=True)
        payload = []
        if docs:
            for d in docs[:10]:
                ext = d.name.split('.')[-1].lower()
                if ext in ['docx', 'xlsx', 'pptx']: payload.append(process_office_file(d))
                elif ext in ['txt', 'py']: payload.append(f"File: {d.name}\n{d.getvalue().decode('utf-8')}")
                elif ext == 'pdf':
                    pdf = fitz.open(stream=d.read(), filetype="pdf")
                    for p in pdf: payload.append(Image.open(io.BytesIO(p.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                else: payload.append(Image.open(d))
            st.success(f"Loaded {len(docs[:10])} files.")

        d_q = st.text_area("Instructions:")
        if st.button("Deep Analysis 🚀") and (payload or d_q):
            # تجميع النصوص من الـ payload لضمان وصولها للموديل
            text_context = "\n".join([item for item in payload if isinstance(item, str)])
            full_query = f"{d_q}\n\nContext from files:\n{text_context}"
            
            res = generate_response(provider, api_key, model_choice, full_query, [p for p in payload if isinstance(p, Image.Image)])
            if res: 
                st.session_state['doc_res'] = res
                st.code(res, language="markdown")
                c1, c2 = st.columns(2)
                c1.download_button("Word 📄", get_word_download(res), "Report.docx")
                ex = get_excel_download(res)
                if ex: c2.download_button("Excel 📊", ex, "Data.xlsx")

    # --- Tab 4: Universal Architect ---
    with tabs[3]:
        u_in = st.text_area("Your Idea:")
        if st.button("Build Professional Prompt"):
            res = generate_response(provider, api_key, model_choice, f"Assign Role, Context, Task for: {u_in}")
            if res: st.code(res)

else:
    st.info("👈 Please select a provider and enter API Key.")
