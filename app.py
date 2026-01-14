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
st.set_page_config(page_title="AI Architect Multi-Power", page_icon="🚀", layout="wide")

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

# --- 2. وظائف المساعدة والمحتوى ---
def process_office_file(file):
    ext = file.name.split('.')[-1].lower()
    content = ""
    try:
        if ext == 'docx':
            doc = Document(file)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'xlsx':
            df = pd.read_excel(file)
            content = "Excel Summary:\n" + df.to_string()
        elif ext == 'pptx':
            prs = Presentation(file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): content += shape.text + "\n"
    except Exception as e: content = f"Error: {e}"
    return f"--- File: {file.name} ---\n{content}"

def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. محرك التوليد ---
def generate_response(provider, api_key, model_name, query, images=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            res = model.generate_content([query] + (images if images else []))
            return res.text
        elif provider == "Groq (Ultra Fast)":
            client = Groq(api_key=api_key)
            if images:
                msgs = [{"role": "user", "content": [{"type": "text", "text": query}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(images[0])}"}}]}]
            else:
                msgs = [{"role": "user", "content": query}]
            res = client.chat.completions.create(messages=msgs, model=model_name)
            return res.choices[0].message.content
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# --- 4. القائمة الجانبية مع خاصية الاكتشاف التلقائي ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    provider = st.selectbox("AI Provider:", ["Google Gemini", "Groq (Ultra Fast)"])
    api_key = st.text_input(f"{provider} API Key:", type="password")
    
    model_choice = None
    if api_key:
        with st.spinner("جاري جلب الموديلات المتاحة حالياً..."):
            try:
                if provider == "Google Gemini":
                    genai.configure(api_key=api_key)
                    # جلب الموديلات التي تدعم توليد المحتوى فقط
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model_choice = st.selectbox("اختر الموديل المتاح في حسابك:", models)
                else:
                    client = Groq(api_key=api_key)
                    # جلب قائمة الموديلات الحية من سيرفر Groq مباشرة
                    groq_models = [m.id for m in client.models.list()]
                    model_choice = st.selectbox("اختر الموديل المتاح في Groq حالياً:", groq_models)
                st.success("✅ تم تحديث قائمة الموديلات بنجاح!")
            except Exception as e:
                st.error("تأكد من الـ API Key أو اتصال الإنترنت.")

# --- 5. واجهة المستخدم الرئيسية ---
if api_key and model_choice:
    st.markdown("<h1 style='text-align: center;'>🪄 AI Architect <span style='color: #00d2ff;'>Multi-Power</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📑 Ultimate Doc Analyzer", "✨ Image Prompts", "📸 Vision Studio", "🧠 Universal Architect"])

    with tabs[0]:
        st.markdown("### 📑 Multi-File Analyzer")
        docs = st.file_uploader("ارفع ملفاتك (PDF, Office, Code, Images)", type=["pdf", "docx", "xlsx", "pptx", "txt", "py", "jpg", "png"], accept_multiple_files=True)
        
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
            st.success(f"تم تحميل {len(docs[:10])} ملفات.")

        d_q = st.text_area("ما هو سؤالك حول هذه الملفات؟")
        if st.button("تحليل عميق 🚀"):
            full_context = "\n".join(payload_text) + "\n\n" + d_q
            res = generate_response(provider, api_key, model_choice, full_context, payload_imgs if payload_imgs else None)
            if res:
                st.code(res, language="markdown")
                st.session_state['last_res'] = res

    # بقية التابات تعمل بنفس المنطق
    with tabs[1]:
        st.markdown("### ✍️ Image Prompts Builder")
        img_idea = st.text_input("فكرة الصورة:")
        if st.button("إنشاء البرومبت"):
            res = generate_response(provider, api_key, model_choice, f"Create a pro image prompt for: {img_idea}")
            if res: st.code(res)

else:
    st.info("👈 يرجى إدخال الـ API Key في القائمة الجانبية للبدء.")
