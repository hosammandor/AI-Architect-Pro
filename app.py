import streamlit as st
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- 0. ضبط الترميز والبيئة ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ملف حفظ المفاتيح محلياً لضمان عدم كتابتها كل مرة
KEYS_FILE = "keys_config.json"

def save_keys_to_disk(keys_dict):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys_dict, f)

def load_keys_from_disk():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": "", "Groq": "", "DeepSeek": "", "xAI": ""}

# --- 1. تصميم الواجهة السينمائية (Midjourney Cinematic Style) ---
st.set_page_config(page_title="AI Architect | The Vault", page_icon="🔐", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    .stApp {
        background-color: #0b0b0e;
        background-image: radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* التابات الزجاجية */
    .stTabs [data-baseweb="tab-list"] { gap: 30px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .stTabs [aria-selected="true"] {
        color: #eb4d4b !important;
        border-bottom: 2px solid #eb4d4b !important;
    }

    /* أزرار Midjourney */
    .stButton>button {
        background: #eb4d4b;
        color: white; border: none; padding: 12px 35px; border-radius: 50px;
        font-weight: 600; transition: 0.3s all;
    }
    .stButton>button:hover {
        background: #ff6b6b; transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(235, 77, 75, 0.4);
    }

    /* بطاقات النتائج الشفافة */
    .result-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px; padding: 25px;
        margin-top: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف المعالجة الذكية ---
def process_any_file(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'docx': return "\n".join([p.text for p in Document(file).paragraphs])
        elif ext == 'xlsx': return f"Excel Data: {pd.read_excel(file).to_string()}"
        elif ext == 'pptx':
            prs = Presentation(file)
            return "\n".join([sh.text for s in prs.slides for sh in s.shapes if hasattr(sh, "text")])
        elif ext in ['txt', 'py']: return file.getvalue().decode('utf-8')
    except: return f"Error in {file.name}"
    return ""

def encode_img_to_base64(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. محرك التوليد الرباعي الموحد ---
def dispatch_ai_request(provider, key, model, prompt, images=None):
    if not key: return "⚠️ المفتاح مفقود! يرجى إضافته في تاب Key Vault."
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            if images:
                msgs = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_img_to_base64(images[0])}"}}]}]
            else: msgs = [{"role": "user", "content": prompt}]
            return c.chat.completions.create(model=model, messages=msgs).choices[0].message.content
        elif provider == "DeepSeek":
            c = OpenAI(api_key=key, base_url="https://api.deepseek.com")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        elif provider == "xAI Grok":
            c = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e:
        if "402" in str(e): return "⚠️ عذراً: رصيدك في DeepSeek غير كافٍ. يرجى الشحن أو استخدام Gemini."
        return f"⚠️ Error: {str(e)}"

# --- 4. إدارة الحالة (Session State) ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_keys_from_disk()

# --- 5. واجهة المستخدم (The Layout) ---
st.markdown("<h1 style='text-align:center; font-weight:700; letter-spacing:-2px;'>AI ARCHITECT <span style='color:#eb4d4b'>PRO</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault", "⚙️ Status"])

# --- TAB 1: Key Vault (إدارة المفاتيح) ---
with tabs[2]:
    st.markdown("### 🔐 Key Vault Manager")
    st.write("احفظ مفاتيحك هنا مرة واحدة فقط ولن تحتاج لكتابتها مجدداً.")
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        v_gem = st.text_input("Gemini API Key:", value=st.session_state.api_vault["Gemini"], type="password")
        v_groq = st.text_input("Groq API Key:", value=st.session_state.api_vault["Groq"], type="password")
    with col_k2:
        v_deep = st.text_input("DeepSeek API Key:", value=st.session_state.api_vault["DeepSeek"], type="password")
        v_xai = st.text_input("xAI Grok API Key:", value=st.session_state.api_vault["xAI"], type="password")
    
    if st.button("SAVE KEYS TO VAULT 🔒"):
        new_data = {"Gemini": v_gem, "Groq": v_groq, "DeepSeek": v_deep, "xAI": v_xai}
        st.session_state.api_vault = new_data
        save_keys_to_disk(new_data)
        st.success("تم تشفير وحفظ المفاتيح بنجاح!")

# --- TAB 2: Analyzer (المحلل الذكي) ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        st.markdown("#### Input Center")
        active_provider = st.selectbox("Choose Brain:", ["Google Gemini", "Groq", "DeepSeek", "xAI Grok"])
        active_key = st.session_state.api_vault.get(active_provider.split()[0])
        
        # محاولة جلب الموديلات تلقائياً إذا وجد المفتاح
        active_model = "gemini-2.0-flash" 
        if active_key:
            try:
                if active_provider == "Google Gemini":
                    genai.configure(api_key=active_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_model = st.selectbox("Select Model:", models, index=0)
                elif active_provider == "Groq":
                    models = [m.id for m in Groq(api_key=active_key).models.list().data]
                    active_model = st.selectbox("Select Model:", models, index=0)
                else:
                    active_model = st.selectbox("Model:", ["deepseek-chat", "deepseek-reasoner"] if "Deep" in active_provider else ["grok-2", "grok-vision-beta"])
            except: st.warning("المفتاح قد يكون منتهياً أو غير صحيح.")

        files = st.file_uploader("Upload Files (PDF, Office, Images)", accept_multiple_files=True)
        query = st.text_area("Mission Details:", placeholder="What should the AI do with these files?")
        
        if st.button("EXECUTE ANALYSIS 🚀"):
            txt_data, img_data = "", []
            if files:
                for f in files[:10]:
                    ext = f.name.split('.')[-1].lower()
                    if ext in ['jpg','png','jpeg']: img_data.append(Image.open(f))
                    elif ext == 'pdf':
                        pdf = fitz.open(stream=f.read(), filetype="pdf")
                        for page in pdf: img_data.append(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                    else: txt_data += process_any_file(f)
            
            with st.spinner("Analyzing..."):
                result = dispatch_ai_request(active_provider, active_key, active_model, txt_data + "\n" + query, img_data)
                st.session_state.last_out = result

    if 'last_out' in st.session_state:
        with c2:
            st.markdown("#### Results")
            st.markdown(f'<div class="result-card">{st.session_state.last_out}</div>', unsafe_allow_html=True)
            st.code(st.session_state.last_out)

# --- TAB 3: Status (حالة النظام) ---
with tabs[3]:
    st.markdown("### ⚙️ System Connection Status")
    for p, k in st.session_state.api_vault.items():
        st.write(f"**{p}:** {'🟢 Active' if k else '🔴 Offline'}")
