import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="AI Pro Architect", page_icon="🪄", layout="wide")

# --- CSS لتطوير الشكل ليكون عصري جداً ---
st.markdown("""
    <style>
    /* تغيير الخلفية العامة */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
        color: #ffffff;
    }
    
    /* تنسيق الحاويات (Cards) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px 10px 0px 0px;
        color: white;
        font-weight: bold;
    }

    /* تحسين شكل الزراير */
    .stButton>button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 10px 20px rgba(0, 210, 255, 0.3);
    }

    /* صندوق النتائج */
    .result-header {
        color: #00d2ff;
        font-weight: bold;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }

    /* القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar الإعدادات ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>💎 Control Center</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key:", type="password", help="Enter your Google AI Studio Key")
    
    current_model = "gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            current_model = st.selectbox("Select Intelligence Level:", models, index=models.index("gemini-1.5-flash") if "gemini-1.5-flash" in models else 0)
        except:
            st.error("Invalid API Key or Connection Issue")

# --- محتوى البرنامج الرئيسي ---
if api_key:
    try:
        model = genai.GenerativeModel(current_model)
        
        st.markdown("<h1 style='text-align: center;'>🪄 AI <span style='color: #00d2ff;'>Architect</span> Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>بوابتك لتحويل الأفكار العادية إلى نتائج بصرية عالمية</p>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["✨ Prompt Engineer", "📸 Vision Studio"])

        # --- Tab 1: مهندس البرومبتات ---
        with tab1:
            col1, col2 = st.columns([1, 1], gap="large")
            
            with col1:
                st.markdown("### ✍️ Describe Your Vision")
                raw_input = st.text_area("", placeholder="مثلاً: بطل خارق بزي فرعوني في مدينة مستقبلية...", height=150)
                target = st.selectbox("Platform Target:", ["Midjourney v6", "DALL-E 3", "Canva Magic Media", "Leonardo AI"])
                generate_btn = st.button("Refine & Optimize")

            with col2:
                st.markdown("### 🚀 Optimized Output")
                if generate_btn and raw_input:
                    with st.spinner("🧠 Engineering the perfect prompt..."):
                        prompt = f"Act as a professional prompt engineer. Transform this idea into a detailed, high-quality English prompt for {target}. Include: artistic style, lighting (cinematic, volumetric), camera angle (low angle, wide shot), and technical specs (8k, photorealistic). Original Idea: {raw_input}"
                        response = model.generate_content(prompt)
                        
                        st.markdown("<div class='result-header'>✅ Ready to Copy:</div>", unsafe_allow_html=True)
                        # استخدام st.code عشان زرار النسخ يظهر تلقائياً
                        st.code(response.text, language="text")
                        st.balloons()
                else:
                    st.info("اكتب فكرتك ودوس على Refine عشان تشوف السحر!")

        # --- Tab 2: استوديو الرؤية ---
        with tab2:
            st.markdown("### 👁️ Image Intelligence & Editing")
            uploaded_file = st.file_uploader("Upload reference image", type=["png", "jpg", "jpeg"])
            
            if uploaded_file:
                v_col1, v_col2 = st.columns(2, gap="medium")
                img = Image.open(uploaded_file)
                
                with v_col1:
                    st.image(img, caption="Original Preview", use_container_width=True)
                
                with v_col2:
                    edit_req = st.text_input("What changes should AI make?", placeholder="E.g. Change the background to Mars...")
                    if st.button("Generate Edit Prompt") and edit_req:
                        with st.spinner("🔍 Analyzing every pixel..."):
                            response = model.generate_content([
                                f"Analyze this image and the request: '{edit_req}'. Create a professional English text-to-image prompt to achieve this exact edit. Focus on keeping the main subject consistent while changing the rest. Use professional keywords.", 
                                img
                            ])
                            st.markdown("<div class='result-header'>🎨 New Edit Prompt:</div>", unsafe_allow_html=True)
                            st.code(response.text, language="text")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("👈 ابدأ بإضافة الـ API Key في القائمة الجانبية")