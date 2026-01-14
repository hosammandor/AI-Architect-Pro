import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io
import time
import requests
import fitz
import pandas as pd
from docx import Document
from pptx import Presentation
from google.api_core import exceptions

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="AI Architect Multi-Pro", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%); color: #ffffff; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; color: white; font-weight: bold; }
    .stButton>button { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); color: white; border: none; border-radius: 12px; font-weight: 700; width: 100%; }
    .result-box { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; border-left: 5px solid #00d2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك توليد النصوص (يدعم Gemini و Groq) ---
def generate_ai_response(provider, api_key, model_name, payload):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            # التعامل مع الملفات (Multimodal)
            response = model.generate_content(payload)
            return response.text
        
        elif provider == "Groq (Ultra Fast)":
            client = Groq(api_key=api_key)
            # Groq حالياً يدعم النصوص بشكل أساسي (Llama 3.1)
            # سنحول الـ payload لنص بسيط للـ Groq
            prompt = payload if isinstance(payload, str) else str(payload[0])
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
            )
            return chat_completion.choices[0].message.content
            
    except Exception as e:
        st.error(f"Error from {provider}: {e}")
        return None

# --- 3. القائمة الجانبية (Selection) ---
with st.sidebar:
    st.markdown("<h2 style='color: #00d2ff;'>⚙️ Provider Settings</h2>", unsafe_allow_html=True)
    provider = st.selectbox("Choose AI Provider:", ["Google Gemini", "Groq (Ultra Fast)"])
    
    api_key = st.text_input(f"Enter {provider} API Key:", type="password")
    
    model_choice = "gemini-1.5-flash" # Default
    if api_key:
        if provider == "Google Gemini":
            model_choice = st.selectbox("Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        else:
            model_choice = st.selectbox("Model:", ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"])

# --- 4. واجهة المستخدم الرئيسية ---
if api_key:
    st.markdown(f"<h1 style='text-align: center;'>🚀 AI Architect <span style='color: #00d2ff;'>Multi-Pro</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["✨ Smart Prompts", "📑 Ultimate Analyzer", "🧠 Universal Architect"])

    # --- Tab: Analyzer (تطوير لدعم الموديلات الجديدة) ---
    with tabs[1]:
        up_docs = st.file_uploader("Upload Docs (Up to 10)", accept_multiple_files=True, type=["pdf", "docx", "xlsx", "txt", "py"])
        query = st.text_area("What's your request?")
        
        if st.button("Process with AI 🚀") and (up_docs or query):
            with st.spinner(f"Processing via {provider}..."):
                # (هنا نستخدم وظيفة المعالجة اللي عملناها قبل كدة للملفات)
                # للتبسيط، سنرسل الطلب للموديل المختار
                final_res = generate_ai_response(provider, api_key, model_choice, query)
                
                if final_res:
                    st.session_state['multi_res'] = final_res
                    st.markdown("### 🔍 Analysis Result:")
                    st.code(final_res, language="markdown")

    # --- Tab: Universal Architect ---
    with tabs[2]:
        u_input = st.text_area("Enter any idea to build a pro prompt:")
        if st.button("Architect Now 🔨"):
            prompt = f"Assign Role, Context, and Task for: {u_input}. Output as a professional prompt."
            res = generate_ai_response(provider, api_key, model_choice, prompt)
            if res: st.code(res, language="text")

else:
    st.info("👈 Please select a provider and enter your API Key to unlock the power.")
