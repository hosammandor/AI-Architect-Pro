import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- 0. ضبط الإعدادات العامة ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KEYS_FILE = "pure_vault.json"

def save_to_vault(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f)
    # تحديث الـ Session State فوراً لضمان مزامنة التابات
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

# --- 1. محرك الإضاءة والثيمات (Theme Engine) ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark (Cinematic)"

with st.sidebar:
    st.markdown("### 🌓 Lighting Mode")
    theme_choice = st.selectbox("Select Mode", ["Dark (Cinematic)", "White (Clean)", "Automatic (Device)"])
    st.session_state.theme = theme_choice

# تخصيص الألوان بناءً على الثيم المختار
if st.session_state.theme == "Dark (Cinematic)":
    main_bg, text_col, card_bg, border_col = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)", "#e0e0e0", "rgba(255,255,255,0.03)", "rgba(255,255,255,0.08)"
elif st.session_state.theme == "White (Clean)":
    main_bg, text_col, card_bg, border_col = "#ffffff", "#1a1a1a", "#f8f9fa", "#dee2e6"
else: # Automatic
    main_bg, text_col, card_bg, border_col = "transparent", "inherit", "rgba(128,128,128,0.05)", "rgba(128,128,128,0.1)"

st.markdown(f"""
    <style>
    .stApp {{ background: {main_bg}; color: {text_col}; transition: 0.5s all; }}
    .result-card {{ 
        background: {card_bg}; 
        border: 1px solid {border_col}; 
        border-radius: 20px; padding: 25px; margin-top: 20px; 
    }}
    .stButton>button {{ background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; width: 100%; border: none; }}
    .stButton>button:hover {{ background: #ff6b6b; transform: scale(1.02); }}
    .account-tag {{ background: rgba(0, 210, 255, 0.1); color: #00d2ff; padding: 4px 12px; border-radius: 8px; font-size: 13px; font-weight: 600; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

# --- 3. وظائف معالجة الملفات والذكاء ---
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

# --- 4. واجهة المستخدم (The Dashboard) ---
st.markdown("<h1 style='text-align:center; letter-spacing:-2px;'>AI ARCHITECT <span style='color:#eb4d4b'>PRO</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault"])

# --- TAB: Key Vault (تم إصلاح المزامنة هنا) ---
with tabs[2]:
    st.markdown("### 🔐 Secure Key Vault")
    st.info("أدخل مفاتيحك مرة واحدة وسيتم ربطها تلقائياً بجميع الموديلات.")
    for p in ["Gemini", "Groq"]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.session_state.api_vault[p]["key"] = st.text_input(f"{p} API Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"v_k_{p}")
        with c2:
            st.session_state.api_vault[p]["label"] = st.text_input(f"Account Label ({p}):", value=st.session_state.api_vault[p]["label"], key=f"v_l_{p}", placeholder="Personal/Work")
    
    if st.button("SAVE AND CONNECT ALL 🔗"):
        save_to_vault(st.session_state.api_vault)

# --- TAB: Analyzer (الربط التلقائي) ---
with tabs[0]:
    col1, col2 = st.columns([1, 1.2], gap="large")
    with col1:
        st.markdown("#### Configuration")
        # التسمية هنا تطابق تماماً مفاتيح القاموس في الـ Vault
        choice = st.selectbox("Select Brain:", ["Gemini", "Groq"])
        acc_info = st.session_state.api_vault.get(choice)
        
        if acc_info and acc_info["key"]:
            st.markdown(f"📍 Connected: <span class='account-tag'>{acc_info['label']}</span>", unsafe_allow_html=True)
            
            # جلب الموديلات تلقائياً فور وجود المفتاح
            try:
                if choice == "Gemini":
                    genai.configure(api_key=acc_info["key"])
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_model = st.selectbox("Select Active Model:", models)
                else:
                    models = [m.id for m in Groq(api_key=acc_info["key"]).models.list().data]
                    active_model = st.selectbox("Select Active Model:", models)
                
                # رفع الملفات والمدخلات
                uploaded = st.file_uploader("Upload Files (PDF, Office, Images)", accept_multiple_files=True)
                query = st.text_area("Your Mission:", placeholder="What should I do?")
                
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
                    
                    with st.spinner("AI is thinking..."):
                        final_res = run_ai_logic(choice, acc_info["key"], active_model, txt_ctx + "\n" + query, img_ctx)
                        st.session_state.last_analysis = final_res
            except Exception as e:
                st.error(f"⚠️ فشل في جلب الموديلات: تأكد من صحة المفتاح في Vault. ({e})")
        else:
            st.warning(f"⚠️ مفتاح {choice} غير موجود. اذهب لتاب Key Vault لحفظه أولاً.")

    if 'last_analysis' in st.session_state:
        with col2:
            st.markdown("#### 🔍 Output")
            st.markdown(f'<div class="result-card">{st.session_state.last_analysis}</div>', unsafe_allow_html=True)
            st.code(st.session_state.last_analysis)
