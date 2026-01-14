# --- تحديث السايد بار لكشف الأخطاء بدقة ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #fff;'>⚙️ CONFIG</h2>", unsafe_allow_html=True)
    provider = st.selectbox("PROVIDER", ["Google Gemini", "Groq (Ultra Fast)", "xAI Grok"])
    api_key = st.text_input("API KEY", type="password")
    
    model_choice = None
    if api_key:
        with st.spinner("Authenticating..."):
            try:
                if provider == "Google Gemini":
                    genai.configure(api_key=api_key)
                    # محاولة جلب الموديلات للتأكد من صحة المفتاح
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model_choice = st.selectbox("MODEL", models, index=0)
                    st.success("✅ Gemini Connected")
                
                elif provider == "Groq (Ultra Fast)":
                    client = Groq(api_key=api_key)
                    # جلب الموديلات الحية من Groq
                    models_data = client.models.list().data
                    models = [m.id for m in models_data]
                    model_choice = st.selectbox("MODEL", models, index=0)
                    st.success("✅ Groq Connected")
                
                elif provider == "xAI Grok":
                    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
                    # جلب موديلات Grok
                    models_data = client.models.list().data
                    models = [m.id for m in models_data]
                    model_choice = st.selectbox("MODEL", models, index=0)
                    st.success("✅ Grok Connected")
                    
            except Exception as e:
                # إظهار رسالة الخطأ الحقيقية للمستخدم
                error_msg = str(e)
                if "401" in error_msg or "API key not found" in error_msg:
                    st.error("❌ المفتاح غير صحيح (Invalid API Key)")
                elif "quota" in error_msg.lower() or "429" in error_msg:
                    st.error("❌ انتهت حصة الاستخدام (Quota Exceeded)")
                else:
                    st.error(f"❌ خطأ تقني: {error_msg}")
