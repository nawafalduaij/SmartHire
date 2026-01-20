import streamlit as st

st.set_page_config(page_title="SmartHire UI", layout="wide")

st.title("SmartHire — واجهة المستخدم")

tab1, tab2 = st.tabs([" رفع وقراءة PDF", " Fake Resume Dataset"])

# -----------------------------
with tab1:
    st.subheader("رفع السيرة الذاتية (PDF)")

    uploaded_pdf = st.file_uploader("ارفع ملف PDF هنا", type=["pdf"])

    st.markdown("### النص المستخرج (سيظهر هنا)")
    extracted_text = st.text_area(
        "محتوى السيرة بعد الاستخراج",
        value="",
        height=420,
        placeholder="بعد ما نربط كود الاستخراج، النص راح يطلع هنا..."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button(" استخراج النص")
    with col2:
        st.button(" حفظ النص")
    with col3:
        st.button(" مسح المحتوى")

# -----------------------------
with tab2:
    st.subheader("تجهيز Fake Resume Dataset")

    st.info("ارفع ملف CSV الخاص بالداتا، وبعدها نربط خطوة التنظيف/التجهيز.")

    uploaded_csv = st.file_uploader("ارفع ملف CSV هنا", type=["csv"])

    colA, colB, colC = st.columns(3)
    with colA:
        st.button(" تحميل الداتا")
    with colB:
        st.button(" تنظيف/تجهيز")
    with colC:
        st.button(" حفظ نسخة processed")

    st.markdown("### معاينة الداتا (Preview)")
    st.dataframe(
        [],
        use_container_width=True
    )
