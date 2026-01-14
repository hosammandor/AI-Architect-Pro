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
    st.rerun() 

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": {"key": "", "label": ""}, "Groq": {"key": "", "label": ""}}

# --- 1. إعدادات الصفحة والسايد بار (Themes) ---
st.set_page_config(page_title="AI Architect | Ultimate Pro", page_icon="🪄", layout="wide")

if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

with st.sidebar:
    st.markdown("### 🎨 UI Aesthetics")
    theme_choice = st.selectbox("Select Theme", ["Dark (Cinematic)", "White (Clean)", "Automatic"], key="theme_toggle")
    st.session_state.theme = theme_choice
    st.markdown("---")
    st.markdown("### 📊 Status")
    for p in ["Gemini", "Groq"]:
        status = "🟢" if st.session_state.api_vault[p]["key"] else "🔴"
        st.write(f"{status} {p}: {st.session_state.api_vault[p]['label']}")

# منطق الألوان
if st.session_state.theme == "Dark (Cinematic)":
    bg, txt, card, brd = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)", "#e0e0e0", "rgba(255,255,255,0.02)", "rgba(255,255,255,0.08)"
elif st.session_state.theme == "White (Clean)":
    bg, txt, card, brd = "#ffffff", "#1a1a1a", "#f8f9fa", "#dee2e6"
else:
    bg, txt, card, brd = "transparent", "inherit", "rgba(128,128,128,0.05)", "rgba(128,128,128,0.1)"

st.markdown(f"<style>.stApp {{ background: {bg}; color: {txt}; }} .result-card {{ background: {card}; border: 1px solid {brd}; border-radius: 20px; padding: 25px; }} .stButton>button {{ background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; width: 100%; }}</style>", unsafe_allow_html=True)

# --- 2. وظائف المحرك ---
def process_any_file(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'docx': return "\n".join([p.text for p in Document(file).paragraphs])
        elif ext == 'xlsx': return f"Excel Data: {pd.read_excel(file).to_string()}"
        elif ext == 'pptx':
            prs = Presentation(file)
            return "\n".join([sh.text for s in prs.slides for sh in s.shapes if hasattr(sh, "text")])
        elif ext in ['txt', 'py']: return file.getvalue().decode('utf-8')
    except: return f"Error reading {file.name}"
    return ""

def ask_ai(provider, key, model, prompt, images=None):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 3. واجهة المستخدم (التابات التشغيلية) ---
st.markdown("<h1 style='text-align:center;'>AI ARCHITECT <span style='color:#eb4d4b'>ULTIMATE</span></h1>", unsafe_allow_html=True)
tabs = st.tabs(["📑 Analyzer", "🎨 Art Studio", "💼 Work Architect", "🔐 Key Vault"])

# --- TAB 1: Analyzer (تعمل بالكامل) ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        prov = st.selectbox("Provider:", ["Gemini", "Groq"], key="analyzer_prov")
        info = st.session_state.api_vault[prov]
        if info["key"]:
            if prov == "Gemini":
                genai.configure(api_key=info["key"])
                models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                mod = st.selectbox("Model:", models)
            else:
                mod = st.selectbox("Model:", [m.id for m in Groq(api_key=info["key"]).models.list().data])
            
            files = st.file_uploader("Upload Files", accept_multiple_files=True)
            q = st.text_area("Question:")
            if st.button("RUN ANALYSIS 🚀"):
                txt_ctx, img_ctx = "", []
                if files:
                    for f in files:
                        ext = f.name.split('.')[-1].lower()
                        if ext in ['jpg','png','jpeg']: img_ctx.append(Image.open(f))
                        elif ext == 'pdf':
                            pdf = fitz.open(stream=f.read(), filetype="pdf")
                            for page in pdf: img_ctx.append(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                        else: txt_ctx += process_any_file(f)
                with st.spinner("Analyzing..."):
                    st.session_state.ans = ask_ai(prov, info["key"], mod, txt_ctx + "\n" + q, img_ctx)
        else: st.warning("قم بإضافة المفتاح في تاب Vault.")

    if 'ans' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_state.ans}</div>', unsafe_allow_html=True)
            st.code(st.session_state.ans)

# --- TAB 2: Art Studio (تعمل بالكامل) ---
with tabs[1]:
    st.markdown("### 🎨 Midjourney Prompt Studio")
    art_q = st.text_input("Describe the image you want:")
    if st.button("GENERATE ART PROMPT ✨"):
        active_key = st.session_state.api_vault["Gemini"]["key"] or st.session_state.api_vault["Groq"]["key"]
        if active_key:
            p = "Gemini" if st.session_state.api_vault["Gemini"]["key"] else "Groq"
            m = "gemini-2.0-flash" if p == "Gemini" else "llama-3.3-70b-versatile"
            with st.spinner("Crafting..."):
                res = ask_ai(p, active_key, m, f"Create a hyper-detailed Midjourney v6 prompt for: {art_q}")
                st.session_state.art_res = res
        else: st.warning("يرجى إدخال مفتاح واحد على الأقل.")
    if 'art_res' in st.session_state:
        st.markdown(f'<div class="result-card">{st.session_state.art_res}</div>', unsafe_allow_html=True)
        st.code(st.session_state.art_res)

# --- TAB 3: Work Architect (تعمل بالكامل) ---
with tabs[2]:
    st.markdown("### 💼 Professional Work Architect")
    job_task = st.text_area("Your simple work request:")
    if st.button("ENGINEER PROMPT 🔨"):
        active_key = st.session_state.api_vault["Gemini"]["key"] or st.session_state.api_vault["Groq"]["key"]
        if active_key:
            p = "Gemini" if st.session_state.api_vault["Gemini"]["key"] else "Groq"
            m = "gemini-2.0-flash" if p == "Gemini" else "llama-3.3-70b-versatile"
            prompt = f"Act as a Prompt Engineer. Turn this task into a pro prompt (Role, Context, Task, Format): {job_task}"
            with st.spinner("Engineering..."):
                res = ask_ai(p, active_key, m, prompt)
                st.session_state.work_res = res
    if 'work_res' in st.session_state:
        st.markdown(f'<div class="result-card">{st.session_state.work_res}</div>', unsafe_allow_html=True)
        st.code(st.session_state.work_res)

# --- TAB 4: Vault ---
with tabs[3]:
    st.markdown("### 🔐 Key Vault")
    for p in ["Gemini", "Groq"]:
        c1, c2 = st.columns([2, 1])
        st.session_state.api_vault[p]["key"] = c1.text_input(f"{p} Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"k_{p}")
        st.session_state.api_vault[p]["label"] = c2.text_input(f"Label:", value=st.session_state.api_vault[p]["label"], key=f"l_{p}")
    if st.button("SAVE CONFIGURATION 💾"):
        save_to_vault(st.session_state.api_vault)
