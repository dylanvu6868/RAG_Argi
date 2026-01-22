# RAG Hệ Thống Hỗ Trợ Nông Nghiệp - Chẩn Đoán Bệnh Lúa

Hệ thống RAG (Retrieval-Augmented Generation) với Hybrid Search cho tài liệu chuyên ngành nông nghiệp và bệnh lúa tiếng Việt.

## 🌾 Giới thiệu

Hệ thống hỗ trợ nông dân và chuyên gia nông nghiệp tra cứu thông tin về:
- **Bệnh hại lúa**: Triệu chứng, nguyên nhân, biện pháp phòng trị
- **Kỹ thuật canh tác**: Cẩm nang trồng trọt, quy trình sản xuất
- **Giải pháp nông nghiệp**: Tư vấn kỹ thuật dựa trên tài liệu chuyên môn

## ✨ Tính năng

- 🔍 **Hybrid Search**: Kết hợp tìm kiếm ngữ nghĩa + từ khóa cho độ chính xác cao
- 🤖 **LLM Tiếng Việt**: Trả lời tự nhiên bằng tiếng Việt (Ollama + Tuanpham/t-visstar-7b)
- 📚 **Tra cứu tài liệu**: Upload PDF về bệnh lúa, cẩm nang trồng trọt
- 📊 **Vector Database**: Qdrant - tìm kiếm nhanh, chính xác
- 🎨 **Giao diện đơn giản**: Streamlit - dễ sử dụng cho nông dân

## 🎯 Ứng dụng thực tế

### Cho nông dân:
- Tra cứu triệu chứng bệnh lúa từ mô tả
- Nhận hướng dẫn phòng trị cụ thể
- Học kỹ thuật canh tác từ cẩm nang

### Cho chuyên gia:
- Tìm kiếm thông tin nhanh trong tài liệu chuyên môn
- Tổng hợp kiến thức từ nhiều nguồn
- Hỗ trợ tư vấn kỹ thuật

## 🏗️ Kiến trúc hệ thống

```
┌──────────────────────┐
│  Upload Tài liệu     │
│  (PDF về bệnh lúa,   │
│   cẩm nang...)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Xử lý & Phân đoạn   │
│  (Character-based    │
│   chunking)          │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌─────────┐
│ Qdrant  │  │  BM25   │
│ Vector  │  │ Index   │
│  Store  │  │(Keyword)│
└────┬────┘  └────┬────┘
     │            │
     │  Câu hỏi   │
     ▼            ▼
     └─────┬──────┘
           │
           ▼
    ┌──────────────┐
    │Hybrid Search │
    │  (Semantic   │
    │  + Keyword)  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   Ollama     │
    │  LLM Model   │
    │ (Vietnamese) │
    └──────┬───────┘
           │
           ▼
    Câu trả lời về
    bệnh lúa/nông nghiệp
```

## 🚀 Cài đặt

### Yêu cầu hệ thống

- **Python**: 3.10 trở lên
- **Docker**: Cho Qdrant vector database
- **Ollama**: Local LLM runtime
- **RAM**: Ít nhất 4GB (khuyến nghị 8GB)

### Hướng dẫn cài đặt

#### Bước 1: Clone repository

```bash
git clone https://github.com/dylanvu6868/RAG_Argi.git
cd RAG_Argi
```

#### Bước 2: Tạo môi trường ảo

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### Bước 3: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

#### Bước 4: Khởi động Qdrant

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/data/qdrant_storage:/qdrant/storage \
  --name qdrant_agriculture \
  qdrant/qdrant
```

#### Bước 5: Cài đặt Ollama và model tiếng Việt

```bash
# Cài Ollama: https://ollama.com/download

# Pull model tiếng Việt
ollama pull Tuanpham/t-visstar-7b:latest
```

#### Bước 6: Chạy ứng dụng

```bash
streamlit run app.py
```

Truy cập: **http://localhost:8501**

## 📖 Hướng dẫn sử dụng

### 1. Upload tài liệu

- Kéo thả file PDF về **bệnh lúa**, **cẩm nang trồng trọt** vào giao diện
- Hệ thống tự động xử lý và đánh index
- Hỗ trợ nhiều file cùng lúc

### 2. Đặt câu hỏi

**Ví dụ câu hỏi:**
- "Triệu chứng bệnh đạo ôn lúa là gì?"
- "Cách phòng trị bệnh khô vằn?"
- "Lúa bị lá vàng, vết bệnh hình thoi là bệnh gì?"
- "Thời điểm bón phân đạm tốt nhất?"

### 3. Xem kết quả

- Câu trả lời chi tiết bằng tiếng Việt
- Nguồn trích dẫn rõ ràng (tên file, số trang)
- Lịch sử hội thoại để tham khảo

## ⚙️ Cấu hình

### File `.env`

```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Để trống nếu dùng local
```

### File `config.py` - Tối ưu cho văn bản nông nghiệp

```python
CHUNK_SIZE = 1000              # 1000 ký tự/chunk
CHUNK_OVERLAP = 200            # Overlap để giữ ngữ cảnh
OLLAMA_MODEL = "Tuanpham/t-visstar-7b:latest"
LLM_TEMPERATURE = 0.3          # Thấp = câu trả lời tập trung
SEARCH_TYPE = "hybrid"         # Kết hợp semantic + keyword
TOP_K_RESULTS = 5              # Lấy 5 đoạn liên quan nhất
```

## 🔧 Công nghệ

| Thành phần | Công nghệ |
|-----------|-----------|
| **Giao diện** | Streamlit |
| **LLM** | Ollama (Tuanpham/t-visstar-7b) |
| **Vector DB** | Qdrant |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Text Chunking** | LangChain RecursiveCharacterTextSplitter |
| **Keyword Search** | BM25Okapi |
| **Fusion** | Reciprocal Rank Fusion (RRF) |

## 📊 Hiệu suất

- **Hybrid Search**: Độ chính xác tăng 15-20% so với chỉ dùng semantic
- **Thời gian trả lời**: 3-5 giây (phụ thuộc cấu hình máy)
- **Bộ nhớ**: ~2GB RAM (embedding model + LLM)
- **Hỗ trợ**: Tiếng Việt chuyên ngành nông nghiệp

## 📁 Cấu trúc dự án

```
RAG_Argi/
├── app.py                    # Giao diện Streamlit
├── rag_engine.py             # Logic RAG + Hybrid Search
├── llm_handler.py            # Tích hợp Ollama
├── config.py                 # Cấu hình hệ thống
├── utils.py                  # Hàm tiện ích
├── requirements.txt          # Dependencies
├── .env                      # Biến môi trường
├── .gitignore               # Git ignore
└── data/
    ├── uploaded_pdfs/        # Tài liệu nông nghiệp
    ├── qdrant_db/           # Vector storage
    └── vector_database_debug/ # Debug info
```

## 💡 Gợi ý tài liệu nên upload

- Cẩm nang bệnh hại lúa
- Quy trình sản xuất lúa theo VietGAP
- Sổ tay kỹ thuật canh tác
- Tài liệu về phân bón, thuốc trừ sâu
- Hướng dẫn phòng trị dịch bệnh

## 🤝 Đóng góp

Dự án mở cho cộng đồng nông nghiệp! Mọi đóng góp đều được hoan nghênh:
1. Fork repository
2. Tạo branch tính năng (`git checkout -b feature/NoiDung`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng NoiDung'`)
4. Push lên branch (`git push origin feature/NoiDung`)
5. Tạo Pull Request

## 📞 Liên hệ & Hỗ trợ

- **GitHub Issues**: Báo lỗi hoặc đề xuất tính năng
- **Repository**: https://github.com/dylanvu6868/RAG_Argi

## 🙏 Cảm ơn

- **Ollama**: https://ollama.com - Local LLM runtime
- **Qdrant**: https://qdrant.tech - Vector database
- **LangChain**: https://langchain.com - RAG framework
- **Model**: Tuanpham/t-visstar-7b - Vietnamese LLM

---

**Phát triển bởi**: Dylan Vu  
**Mục đích**: Hỗ trợ nông dân & chuyên gia nông nghiệp Việt Nam
