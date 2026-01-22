import streamlit as st
import os
from pathlib import Path

import config
from rag_engine import RAGEngine
from llm_handler import LLMHandler
from utils import format_source_reference, highlight_text


# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .answer-box {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .source-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None
    st.session_state.llm_handler = None
    st.session_state.chat_history = []
    st.session_state.initialized = False

    # Auto-initialize on startup
    try:
        with st.spinner("🚀 Đang khởi động hệ thống..."):
            st.session_state.rag_engine = RAGEngine()
            st.session_state.llm_handler = LLMHandler()
            st.session_state.initialized = True
    except Exception as e:
        st.error(f"Lỗi khởi động: {str(e)}")


def upload_pdfs(uploaded_files):
    if not uploaded_files:
        return
    
    total_chunks = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            pdf_path = config.PDF_UPLOAD_DIR / uploaded_file.name
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            status_text.text(f"Đang xử lý: {uploaded_file.name}")
            
            # Process PDF
            chunks = st.session_state.rag_engine.process_pdf(str(pdf_path))
            total_chunks += chunks
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        except Exception as e:
            st.error(f"Lỗi xử lý {uploaded_file.name}: {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    
    if total_chunks > 0:
        st.success(f"✅ Đã xử lý {len(uploaded_files)} tài liệu, tạo {total_chunks} chunks!")
    else:
        st.info("Các tài liệu đã được xử lý trước đó.")


def process_query(query: str, top_k: int):
    try:
        with st.spinner("🔍 Đang tìm kiếm tài liệu liên quan..."):
            results = st.session_state.rag_engine.search(
                query=query,
                search_type="hybrid",
                k=top_k
            )
        
        if not results:
            st.warning("Không tìm thấy tài liệu liên quan.")
            return
        docs = [doc for doc, score in results]
        with st.spinner("🤖 Đang tạo câu trả lời..."):
            response = st.session_state.llm_handler.generate_answer(
                query=query,
                context_docs=docs,
                chat_history=st.session_state.chat_history
            )
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.markdown("### 🤖 Câu trả lời")
        st.markdown(response['answer'])
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("### 📚 Nguồn tham khảo")
        for i, source in enumerate(response['sources'], 1):
            with st.expander(f"Nguồn {i}: {source['source']} (trang {source['page']})"):
                highlighted = highlight_text(source['content'], query, max_length=500)
                st.markdown(f'<div class="source-box">{highlighted}</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({
            'role': 'user',
            'content': query
        })
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response['answer']
        })
    
    except Exception as e:
        st.error(f"Lỗi xử lý câu hỏi: {str(e)}")


def main():
    st.markdown('<h1 class="main-header">📚 Hệ thống RAG - Hỏi đáp Tài liệu PDF</h1>', unsafe_allow_html=True)
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        if st.session_state.initialized and st.session_state.rag_engine:
            stats = st.session_state.rag_engine.get_stats()
            
            st.metric("📄 Tổng số tài liệu", stats['total_documents'])
            st.metric("📦 Tổng số chunks", stats['total_chunks'])           
            st.divider()
            top_k = st.slider(
                "Số lượng kết quả",
                min_value=1,
                max_value=10,
                value=5,
                help="Số lượng đoạn văn bản liên quan nhất"
            )
            
            st.divider()
            if st.button("🗑️ Xóa toàn bộ dữ liệu", use_container_width=True, type="secondary"):
                if st.session_state.rag_engine:
                    st.session_state.rag_engine.clear_all()
                    st.session_state.chat_history = []
                    st.success("Đã xóa toàn bộ dữ liệu!")
                    st.rerun()
        else:
            top_k = 5
    if not st.session_state.initialized:
        st.error("Hệ thống chưa được khởi tạo thành công.")
        return
    st.header("📤 Upload Tài liệu PDF")
    uploaded_files = st.file_uploader(
        "Kéo thả file PDF vào đây hoặc click để chọn",
        type=['pdf'],
        accept_multiple_files=True,
        help="Bạn có thể upload bao nhiêu file PDF tùy thích"
    )
    
    if uploaded_files:
        if st.button("🔄 Xử lý tài liệu", use_container_width=True, type="primary"):
            upload_pdfs(uploaded_files)
            st.rerun()
    
    st.divider()
    st.header("💬 Đặt câu hỏi")
    stats = st.session_state.rag_engine.get_stats()
    if not stats['has_data']:
        st.warning("⚠️ Chưa có tài liệu nào. Vui lòng upload PDF trước.")
        return
    
    query = st.text_input(
        "Nhập câu hỏi của bạn:",
        placeholder="Ví dụ: Tài liệu này nói về gì?",
        key="query_input"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        search_button = st.button("🔍 Tìm kiếm", use_container_width=True, type="primary")
    with col2:
        clear_history = st.button("🗑️ Xóa lịch sử chat", use_container_width=True)
    
    if clear_history:
        st.session_state.chat_history = []
        st.success("Đã xóa lịch sử chat!")
    
    if search_button and query:
        process_query(query, top_k)
    if st.session_state.chat_history:
        st.divider()
        with st.expander("📜 Lịch sử hội thoại", expanded=False):
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"**🧑 Người dùng:** {msg['content']}")
                else:
                    st.markdown(f"**🤖 Trợ lý:** {msg['content']}")
                st.markdown("---")

if __name__ == "__main__":
    main()