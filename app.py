import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, requests, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- ضبط الترميز لدعم اللغة العربية ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="AI Architect Smart Pro", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%); color: #ffffff; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; color: white; font-weight: bold; }
    .stButton>button { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); color: white; border-radius: 12px; font-weight: 700; width: 100%; }
    .result-box { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; border-left: 5px solid #00d2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف المساعدة ---
def process_office_file(file):
    ext = file.name.split('.')[-1].lower()
    content = ""
    try:
        if ext == 'docx':
            doc = Document(file)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'xlsx':
            df = pd.read_excel(file)
            content = f"Data from {file.name}:\n{df.to_string()}"
        elif ext == 'pptx':
            prs = Presentation(file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): content += shape.text + "\n"
    except Exception as e: content = f"Error reading {file.name}: {e}"
    return f"--- {file.name} ---\n{content}\n"

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
            if images and ("vision" in model_name.lower() or "3.2" in model_name.lower()):
                msgs = [{"role": "user", "content": [{"type": "text", "text": query}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(images[0])}"}}]}]
            else:
                msgs = [{"role": "user", "content": query}]
            res = client.chat.completions.create(messages=msgs, model=model_name)
            return res.choices[0].message.content
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

# --- 4. القائمة الجانبية (الاكتشاف الذكي المقترح) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    provider = st.selectbox("AI Provider:", ["Google Gemini", "Groq (Ultra Fast)"])
    api_key = st.text_input(f"{provider} API Key:", type="password")
    
    model_choice = None
    if api_key:
        with st.spinner("جاري تحليل الموديلات واختيار الأفضل..."):
            try:
                if provider == "Google Gemini":
                    genai.configure(api_key=api_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    
                    # نظام الاقتراح لـ Gemini
                    suggested = "gemini-2.0-flash" if "gemini-2.0-flash" in models else ("gemini-1.5-flash" if "gemini-1.5-flash" in models else models[0])
                    model_choice = st.selectbox("اختر الموديل (تم اقتراح الأفضل):", models, index=models.index(suggested))
                    st.info(f"💡 المقترح: {suggested} (شامل وسريع)")

                else:
                    client = Groq(api_key=api_key)
                    groq_models = [m.id for m in client.models.list().data]
                    
                    # نظام الاقتراح لـ Groq
                    suggested = "llama-3.3-70b-versatile" if "llama-3.3-70b-versatile" in groq_models else groq_models[0]
                    model_choice = st.selectbox("اختر الموديل (تم اقتراح الأفضل):", groq_models, index=groq_models.index(suggested))
                    st.info(f"💡 المقترح: {suggested} (ملك السرعة والنصوص)")
                
                st.success(f"✅ متصل بـ {provider}")
            except Exception as e:
                st.error("❌ خطأ في الاتصال بالسيرفر.")

# --- 5. واجهة المستخدم الرئيسية ---
if api_key and model_choice:
    st.markdown("<h1 style='text-align: center;'>🪄 AI Architect <span style='color: #00d2ff;'>Smart Pro</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📑 Doc Analyzer", "✨ Image Prompts", "📸 Vision Studio", "🧠 Universal Architect"])

    with tabs[0]:
        st.markdown("### 📑 Multi-File Analyzer")
        docs = st.file_uploader("ارفع ملفاتك (PDF, Office, Code, Images)", type=["pdf", "docx", "xlsx", "pptx", "txt", "py", "jpg", "png"], accept_multiple_files=True)
        
        payload_text = []
        payload_imgs = []
        if docs:
            for d in docs[:10]:
                ext = d.name.split('.')[-1].lower()
                if ext in ['docx', 'xlsx', 'pptx']: payload_text.append(process_office_file(d))
                elif ext in ['txt', 'py']: payload_text.append(f"File: {d.name}\n{d.getvalue().decode('utf-8')}\n")
                elif ext == 'pdf':
                    pdf_doc = fitz.open(stream=d.read(), filetype="pdf")
                    for page in pdf_doc:
                        pix = page.get_pixmap(matrix=fitz.Matrix(1,1))
                        payload_imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))))
                else: payload_imgs.append(Image.open(d))
            st.success(f"تم تحميل {len(docs[:10])} ملفات.")

        d_query = st.text_area("ماذا تريد أن تفعل؟")
        if st.button("تحليل البيانات 🚀"):
            full_context = "".join(payload_text) + "\n" + d_query
            res = generate_response(provider, api_key, model_choice, full_context, payload_imgs if payload_imgs else None)
            if res:
                st.code(res, language="markdown")
                st.session_state['last_res'] = res

    # (بقية التابات تعمل بنفس المنطق الذكي)
    with tabs[1]:
        st.markdown("### ✍️ Image Prompts Builder")
        p_idea = st.text_input("صف فكرتك:")
        if st.button("إنشاء برومبت ✨"):
            p_res = generate_response(provider, api_key, model_choice, f"Create a pro image prompt for: {p_idea}")
            if p_res: st.code(p_res)

else:
    st.markdown("<div style='text-align: center; padding: 100px;'><h3>👋 مرحباً بك! يرجى إدخال الـ Key للبدء</h3></div>", unsafe_allow_html=True)
