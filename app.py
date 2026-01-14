import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- 0. إعدادات النظام ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KEYS_FILE = "pure_vault.json"

def save_to_vault(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f)
    st.session_state.api_vault = data
    st.success("✅ تم الحفظ والربط بنجاح! جاري التحديث...")
    time.sleep(1)
    st.rerun() 

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": {"key": "", "label": ""}, "Groq": {"key": "", "label": ""}}

# --- 1. محرك الثيمات وتصميم Midjourney ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark (Cinematic)"

st.set_page_config(page_title="AI Architect | Cinematic", page_icon="🎨", layout="wide")

with st.sidebar:
    st.markdown("### 🎨 UI Aesthetics")
    theme_choice = st.selectbox("Select Theme", ["Dark (Cinematic)", "White (Clean)", "Automatic (Device)"])
    st.session_state.theme = theme_choice

if st.session_state.theme == "Dark (Cinematic)":
    bg_gradient = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)"
    text_color = "#e0e0e0"
    card_bg = "rgba(255, 255, 255, 0.02)"
    border_color = "rgba(255, 255, 255, 0.08)"
    sidebar_bg = "rgba(10, 10, 15, 0.95)"
elif st.session_state.theme == "White (Clean)":
    bg_gradient = "#ffffff"
    text_color = "#1a1a1a"
    card_bg = "#f8f9fa"
    border_color = "#dee2e6"
    sidebar_bg = "#f0f2f6"
else:
    bg_gradient = "transparent"
    text_color = "inherit"
    card_bg = "rgba(128, 128, 128, 0.05)"
    border_color = "rgba(128, 128, 128, 0.1)"
    sidebar_bg = "inherit"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    .stApp {{ background: {bg_gradient}; color: {text_color}; font-family: 'Inter', sans-serif; transition: 0.5s all; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_color}; backdrop-filter: blur(20px); }}
    .stTabs [aria-selected="true"] {{ color: #eb4d4b !important; border-bottom: 2px solid #eb4d4b !important; }}
    .stButton>button {{ background: linear-gradient(135deg, #eb4d4b 0%, #ff6b6b 100%); color: white; border-radius: 50px; font-weight: 600; width: 100%; box-shadow: 0 4px 15px rgba(235, 77, 75, 0.3); }}
    .result-card {{ background: {card_bg}; border: 1px solid {border_color}; border-radius: 20px; padding: 25px; margin-top: 25px; box-shadow: 0 15px 40px rgba(0,0,0,0.2); backdrop-filter: blur(10px); }}
    .copy-label {{ font-size: 12px; color: #888; margin-top: 10px; margin-bottom: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

# --- 3. وظائف المعالجة ---
def process_file_content(file):
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

def run_ai_logic(provider, key, model, prompt, images=None):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 4. واجهة المستخدم ---
st.markdown("<h1 style='text-align:center; font-weight: 700; letter-spacing:-2px;'>AI ARCHITECT <span style='color:#eb4d4b'>PRO</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault"])

# --- TAB: Analyzer ---
with tabs[0]:
    col1, col2 = st.columns([1, 1.2], gap="large")
    with col1:
        choice = st.selectbox("Select Brain:", ["Gemini", "Groq"])
        acc_info = st.session_state.api_vault.get(choice)
        
        if acc_info and acc_info["key"]:
            try:
                if choice == "Gemini":
                    genai.configure(api_key=acc_info["key"])
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_model = st.selectbox("Select Active Model:", models)
                else:
                    models = [m.id for m in Groq(api_key=acc_info["key"]).models.list().data]
                    active_model = st.selectbox("Select Active Model:", models)
                
                uploaded = st.file_uploader("Upload Files", accept_multiple_files=True)
                query = st.text_area("Your Mission:", placeholder="Enter your instructions...")
                
                if st.button("EXECUTE ANALYSIS 🚀"):
                    txt_ctx, img_ctx = "", []
                    if uploaded:
                        for f in uploaded:
                            ext = f.name.split('.')[-1].lower()
                            if ext in ['jpg','png','jpeg']: img_ctx.append(Image.open(f))
                            elif ext == 'pdf':
                                pdf_doc = fitz.open(stream=f.read(), filetype="pdf")
                                for page in pdf_doc: img_ctx.append(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                            else: txt_ctx += process_file_content(f)
                    
                    with st.spinner("Analyzing..."):
                        final_res = run_ai_logic(choice, acc_info["key"], active_model, txt_ctx + "\n" + query, img_ctx)
                        st.session_state.last_analysis = final_res
            except Exception as e: st.error(f"⚠️ {e}")
        else: st.warning("⚠️ يرجى إعداد المفاتيح في تاب Vault.")

    if 'last_analysis' in st.session_state:
        with col2:
            st.markdown("#### 🔍 Results")
            # عرض النتيجة بشكل سينمائي
            st.markdown(f'<div class="result-card">{st.session_state.last_analysis}</div>', unsafe_allow_html=True)
            
            # --- ميزة النسخ (Copyable Block) ---
            st.markdown('<p class="copy-label">📋 Click top-right to copy text:</p>', unsafe_allow_html=True)
            st.code(st.session_state.last_analysis, language=None)

# --- TAB: Studio ---
with tabs[1]:
    st.markdown("#### 🎨 Prompt Studio")
    art_idea = st.text_input("Enter your creative concept:")
    if st.button("GENERATE PROMPT ✨"):
        key = st.session_state.api_vault["Gemini"]["key"] or st.session_state.api_vault["Groq"]["key"]
        if key:
            res = run_ai_logic("Gemini" if st.session_state.api_vault["Gemini"]["key"] else "Groq", key, "gemini-2.0-flash", f"Midjourney v6 prompt for: {art_idea}")
            st.markdown(f'<div class="result-card">{res}</div>', unsafe_allow_html=True)
            st.markdown('<p class="copy-label">📋 Copy prompt:</p>', unsafe_allow_html=True)
            st.code(res, language=None)

# --- TAB: Vault ---
with tabs[2]:
    st.markdown("### 🔐 Secure Vault")
    for p in ["Gemini", "Groq"]:
        c1, c2 = st.columns([2, 1])
        with c1: st.session_state.api_vault[p]["key"] = st.text_input(f"{p} API Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"v_k_{p}")
        with c2: st.session_state.api_vault[p]["label"] = st.text_input(f"{p} Label:", value=st.session_state.api_vault[p]["label"], key=f"v_l_{p}")
    if st.button("SAVE AND CONNECT 🔗"): save_to_vault(st.session_state.api_vault)
