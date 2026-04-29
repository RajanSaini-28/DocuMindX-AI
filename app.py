import streamlit as st
from utils import extract_text_from_pdf, summarize_text, generate_questions, smart_ask, create_vector_store

st.set_page_config(page_title="DocuMindX AI", page_icon="🚀", layout="wide")

# ===========================
# 🌙 DARK MODE
# ===========================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=True)

bg = "#0e1117" if dark_mode else "#ffffff"
text = "white" if dark_mode else "black"

# ===========================
# 🎨 CSS
# ===========================
st.markdown(f"""
<style>
body {{
    background-color: {bg};
    color: {text};
}}

.title {{
    width: 100%;
    text-align: center;
    font-size: 55px;
    font-weight: bold;
    margin-top: 10px;
    margin-bottom: 5px;
    background: linear-gradient(90deg, #00C9FF, #92FE9D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.tagline {{
    width: 100%;
    text-align: center;
    font-size: 18px;
    color: gray;
    margin-bottom: 20px;
}}

.card {{
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    transition: 0.3s;
}}

.card:hover {{
    transform: scale(1.05);
}}
</style>
""", unsafe_allow_html=True)

# ===========================
# SESSION STATE
# ===========================
if "all_text" not in st.session_state:
    st.session_state.all_text = ""

if "chunks" not in st.session_state:
    st.session_state.chunks = []

if "index" not in st.session_state:
    st.session_state.index = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

# ===========================
# SIDEBAR
# ===========================
st.sidebar.title("⚙️ Settings")

if st.sidebar.button("🔄 New Upload"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📜 History")

if st.session_state.history:
    for i, item in enumerate(st.session_state.history[-5:]):
        with st.sidebar.expander(f"Item {i+1}"):
            st.write(item[:200])
else:
    st.sidebar.write("No history yet")

# ===========================
# 🚀 HERO (CENTERED FIXED)
# ===========================
st.markdown("""
<div style="text-align: center;">
    <div class="title">🚀 DocuMindX AI</div>
    <div class="tagline">
        Smart Document Intelligence — Chat, Analyze & Master PDFs
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===========================
# 📊 DASHBOARD
# ===========================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="card">📄<br><b>Multi-PDF Analysis</b></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">🤖<br><b>AI Chat</b></div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card">🔍<br><b>Semantic Search</b></div>', unsafe_allow_html=True)

st.markdown("---")

# ===========================
# 📤 FILE UPLOAD
# ===========================
files = st.file_uploader("📤 Upload PDFs", type="pdf", accept_multiple_files=True)

if files:
    combined_text = ""

    with st.spinner("📖 Processing PDFs..."):
        for f in files:
            text = extract_text_from_pdf(f)
            if text:
                combined_text += text + "\n"

    st.session_state.all_text = combined_text

    chunks, index = create_vector_store(combined_text)

    if index is None or len(chunks)==0:
        st.error("❌ No valid text found in PDF. Try another file.")
        st.stop()
    st.session_state.chunks = chunks
    st.session_state.index = index

    st.success(f"✅ {len(files)} files processed successfully!")

# ===========================
# 📊 TABS
# ===========================
tab1, tab2, tab3 = st.tabs(["📊 Insights", "🎯 Questions", "💬 AI Chat"])

# ===========================
# 📝 SUMMARY
# ===========================
with tab1:
    if st.session_state.all_text:
        if st.button("✨ Generate Summary"):
            summary = summarize_text(st.session_state.all_text)
            st.write(summary)
            st.session_state.history.append(summary)
    else:
        st.warning("📌 Upload PDFs first")

# ===========================
# ❓ QUESTIONS
# ===========================
with tab2:
    if st.session_state.all_text:
        if st.button("🎯 Generate Questions"):
            questions = generate_questions(st.session_state.all_text)
            st.write(questions)
            st.session_state.history.append(questions)
    else:
        st.warning("📌 Upload PDFs first")

# ===========================
# 💬 CHAT (MEMORY + SOURCE)
# ===========================
with tab3:
    st.subheader("💬 Chat with your PDFs")

    if st.session_state.index:

        # Show chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Ask anything from your PDFs..."):

            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤖 Thinking..."):

                    answer, sources = smart_ask(
                        st.session_state.chunks,
                        st.session_state.index,
                        prompt
                    )

                    st.markdown(answer)

                    # 📄 Sources
                    with st.expander("📄 Sources used"):
                        for i, s in enumerate(sources):
                            st.write(f"🔹 Source {i+1}:")
                            st.write(s[:200] + "...")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            st.session_state.history.append(answer)

    else:
        st.warning("📌 Upload PDFs first")

# ===========================
# FOOTER
# ===========================
st.markdown("---")
st.markdown("""
<p style='text-align:center; color: gray;'>
🚀 DocuMindX AI | Smart Document Intelligence Platform
</p>
""", unsafe_allow_html=True)
