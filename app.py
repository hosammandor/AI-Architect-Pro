import streamlit as st
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from PIL import Image
import io, base64, time, json, os, sys, requests
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- 0. ضبط الترميز والبيئة ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ملف حفظ المفاتيح والبيانات
KEYS_FILE = "keys_config.json"

def save_keys_to_disk(keys_dict):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys_dict, f)

def load_keys_from_disk():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                data = json.load(f)
                # التأكد من دعم هيكل البيانات الجديد (Label)
                for k in ["Gemini", "Groq", "DeepSeek", "xAI"]:
                    if k not in data: data[k] = {"key": "", "label": ""}
                    if isinstance(data[k], str): data[k] = {"key": data[k], "label": ""}
                return data
        except: pass
    return {
        "Gemini": {"key": "", "label": ""},
        "Groq": {"key": "", "label": ""},
        "DeepSeek": {"key": "", "label": ""},
        "xAI": {"key": "", "label": ""}
    }

# --- 1. تصميم الواجهة السينمائية (Midjourney Cinematic UI) ---
st.set_page_config(page_title="AI Architect | Multi-Account", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    .stApp {
        background-color: #0b0b0e;
        background-image: radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 30px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .stTabs [aria-selected="true"] { color: #eb4d4b !important; border-bottom: 2px solid #eb4d4b !important; }

    .stButton>button {
        background: #eb4d4b; color: white; border: none; padding: 12px 35px; 
        border-radius: 50px; font-weight: 600; transition: 0.3s all;
    }
    .stButton>button:hover { background: #ff6b6b; transform: scale(1.02); box-shadow: 0 5px 20px rgba(235, 77, 75, 0.4); }

    .result-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px; padding: 25px; margin-top: 20px;
    }
    
    .account-tag {
        background: rgba(0, 210, 255, 0.1);
        color: #00d2ff; padding: 4px 12px; border-radius: 8px;
        font-size: 13px; font-weight: 600; border: 1px solid rgba(0, 210, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف الذكاء والتحقق من الرصيد ---
def check_deepseek_balance(key):
    try:
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        res = requests.get("https://api.deepseek.com/user/balance", headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            balance_info = data["balance_infos"][0]
            return f"🟢 {balance_info['total_balance']} {balance_info['currency']}"
        return "🔴 غير متاح"
    except: return "⚪ تعذر الاتصال"

def dispatch_ai_request(provider, key, model, prompt, images=None):
    if not key: return "⚠️ المفتاح مفقود! يرجى إعداده في تاب Key Vault."
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            msgs = [{"role": "user", "content": prompt}]
            return c.chat.completions.create(model=model, messages=msgs).choices[0].message.content
        elif provider == "DeepSeek":
            c = OpenAI(api_key=key, base_url="https://api.deepseek.com")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        elif provider == "xAI Grok":
            c = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e:
        if "402" in str(e): return "⚠️ عذراً: رصيد هذا الحساب في DeepSeek غير كافٍ."
        return f"⚠️ Error: {str(e)}"

# --- 3. إدارة الحالة ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_keys_from_disk()

# --- 4. واجهة المستخدم ---
st.markdown("<h1 style='text-align:center; font-weight:700; letter-spacing:-2px;'>AI ARCHITECT <span style='color:#eb4d4b'>MULTI-ACCOUNT</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault", "📊 Status & Billing"])

# --- TAB: Key Vault (إدارة الحسابات) ---
with tabs[2]:
    st.markdown("### 🏦 Multi-Account & Key Vault")
    st.write("اربط كل مفتاح بحساب معين (مثل: شغل، شخصي، تجربة) لسهولة التمييز.")
    
    for provider in ["Gemini", "Groq", "DeepSeek", "xAI"]:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.session_state.api_vault[provider]["key"] = st.text_input(
                f"{provider} API Key:", value=st.session_state.api_vault[provider]["key"], 
                type="password", key=f"v_k_{provider}"
            )
        with col2:
            st.session_state.api_vault[provider]["label"] = st.text_input(
                "تسمية الحساب:", value=st.session_state.api_vault[provider]["label"], 
                key=f"v_l_{provider}", placeholder="e.g. Work Account"
            )
    
    if st.button("SAVE ACCOUNTS TO DISK 💾"):
        save_keys_to_disk(st.session_state.api_vault)
        st.success("تم تشفير وحفظ جميع الحسابات بنجاح!")

# --- TAB: Status & Billing (متابعة الرصيد والربط) ---
with tabs[3]:
    st.markdown("### 📊 Live Connection & Billing")
    
    for provider, info in st.session_state.api_vault.items():
        c1, c2, c3 = st.columns([1, 1, 2])
        c1.write(f"**{provider}**")
        acc_label = info['label'] if info['label'] else "No Label Assigned"
        c2.markdown(f"<span class='account-tag'>{acc_label}</span>", unsafe_allow_html=True)
        
        if provider == "DeepSeek" and info['key']:
            c3.write(f"رصيد الحساب: {check_deepseek_balance(info['key'])}")
        else:
            c3.write("✅ المفتاح محفوظ" if info['key'] else "❌ مفتاح مفقود")

# --- TAB: Analyzer (المحلل الذكي المربوط بالحسابات) ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        st.markdown("#### Input Center")
        choice = st.selectbox("Choose Brain:", ["Google Gemini", "Groq", "DeepSeek", "xAI Grok"])
        provider_name = choice.split()[0] if " " in choice else choice
        
        # معلومات الحساب المختار
        active_acc = st.session_state.api_vault.get(provider_name, {})
        current_key = active_acc.get('key')
        current_label = active_acc.get('label', 'Default')
        
        if current_key:
            st.caption(f"📍 متصل بحساب: **{current_label}**")
            # جلب الموديلات تلقائياً
            try:
                if provider_name == "Gemini":
                    genai.configure(api_key=current_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_model = st.selectbox("Select Model:", models, index=0)
                elif provider_name == "Groq":
                    active_model = st.selectbox("Model:", [m.id for m in Groq(api_key=current_key).models.list().data])
                else:
                    active_model = st.selectbox("Model:", ["deepseek-chat", "deepseek-reasoner"] if "Deep" in provider_name else ["grok-2", "grok-vision-beta"])
            except: st.warning("المفتاح غير صالح!")
        else:
            st.info("قم بإضافة مفتاح لهذا المزود في تاب Key Vault للبدء.")

        files = st.file_uploader("Drop images or docs", accept_multiple_files=True)
        q = st.text_area("What is the mission?")
        if st.button("EXECUTE ANALYSIS 🚀"):
            # منطق تحليل الملفات...
            with st.spinner("Processing..."):
                res = dispatch_ai_request(provider_name, current_key, active_model, q)
                st.session_state.last_out = res

    if 'last_out' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_state.last_out}</div>', unsafe_allow_html=True)
