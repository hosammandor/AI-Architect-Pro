import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io
import base64
import requests
import fitz
import pandas as pd
from docx import Document
from pptx import Presentation

# --- 1. إعدادات الترميز والصفحة ---
# نضمن أن النصوص العربية يتم التعامل معها كـ UTF-8
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

st.set_page_config(page_title="AI Architect Multi-Pro", page_icon="🚀", layout="wide")

# --- 2. وظائف مساعدة لمعالجة الصور لـ Groq ---
def encode_image_to_base64(image):
    buffered = io.BytesIO()
    # تحويل الصورة لـ RGB لضمان التوافق مع JPEG
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. محرك التوليد المطور (يدعم العربية و Groq Vision) ---
def generate_ai_response(provider, api_key, model_name, text_query, images=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            payload = [text_query] + (images if images else [])
            response = model.generate_content(payload)
            return response.text
        
        elif provider == "Groq (Ultra Fast)":
            client = Groq(api_key=api_key)
            messages = []
            
            # إذا كان الموديل يدعم الرؤية (Vision) وفيه صور مرفوعة
            if "vision" in model_name.lower() and images:
                base64_image = encode_image_to_base64(images[0])
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_query},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            else:
                # محادثة نصية عادية (تدعم العربية بترميز UTF-8 تلقائياً)
                messages = [{"role": "user", "content": text_query}]

            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
            )
            return chat_completion.choices[0].message.content
            
    except Exception as e:
        st.error(f"خطأ من {provider}: {str(e)}")
        return None

# --- 4. القائمة الجانبية ---
with st.sidebar:
    st.markdown("<h2 style='color: #00d2ff;'>⚙️ Provider Settings</h2>", unsafe_allow_html=True)
    provider = st.selectbox("Choose AI Provider:", ["Google Gemini", "Groq (Ultra Fast)"])
    api_key = st.text_input(f"Enter {provider} API Key:", type="password")
    
    if api_key:
        if provider == "Google Gemini":
            model_choice = st.selectbox("Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        else:
            # إضافة موديلات Groq Vision الجديدة والمجانية
            model_choice = st.selectbox("Model:", [
                "llama-3.2-11b-vision-preview",  # يدعم الصور!
                "llama-3.1-70b-versatile", 
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768"
            ])

# --- 5. واجهة المستخدم ---
if api_key:
    st.markdown("<h1 style='text-align: center;'>🚀 AI Architect <span style='color: #00d2ff;'>Multi-Pro</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📑 Ultimate Analyzer", "🧠 Universal Architect"])

    with tabs[0]:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            up_docs = st.file_uploader("Upload Files (Images, PDF, Text)", accept_multiple_files=True)
            query = st.text_area("What is your request? (يدعم العربية)", placeholder="اكتب سؤالك هنا...")
        
        if st.button("Execute Analysis 🚀"):
            if query:
                with st.spinner(f"Processing via {provider}..."):
                    # تجهيز البيانات
                    images_list = []
                    text_context = query
                    
                    if up_docs:
                        for doc in up_docs:
                            ext = doc.name.split('.')[-1].lower()
                            if ext in ['jpg', 'jpeg', 'png']:
                                images_list.append(Image.open(doc))
                            # (يمكن إضافة باقي منطق معالجة PDF/Office هنا كما في النسخ السابقة)

                    res = generate_ai_response(provider, api_key, model_choice, text_context, images_list)
                    
                    if res:
                        st.session_state['res'] = res
                        with col2:
                            st.markdown("### 🔍 Result:")
                            st.code(res, language="markdown")
            else:
                st.warning("Please enter a question first!")
else:
    st.info("👈 Please enter your API Key in the sidebar.")
