from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama

import config


class LLMHandler:
    def __init__(self):
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        try:
            self.llm = Ollama(
                model=config.OLLAMA_MODEL,
                temperature=config.LLM_TEMPERATURE,
            )
            print(f"Initialized Ollama with model: {config.OLLAMA_MODEL}")
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            raise
    
    def generate_answer(
        self, 
        query: str, 
        context_docs: List[Document],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        if not context_docs:
            return {
                'answer': "Tôi không tìm thấy thông tin liên quan trong tài liệu để trả lời câu hỏi này.",
                'sources': []
            }

        context_parts = []
        sources = []
        
        for i, doc in enumerate(context_docs, 1):
            source_name = doc.metadata.get('source', 'Unknown')
            page_num = doc.metadata.get('page', 0) + 1
            content = doc.page_content
            
            context_parts.append(f"[Tài liệu {i}] {source_name} (trang {page_num}):\n{content}")
            sources.append({
                'source': source_name,
                'page': page_num,
                'content': content
            })
        
        context = "\n\n".join(context_parts)
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_parts = []
            for msg in chat_history[-3:]: 
                role = "Người dùng" if msg['role'] == 'user' else "Trợ lý"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n".join(history_parts)
        template = """Bạn là trợ lý AI hữu ích.

{history_section}

Thông tin từ tài liệu:
{context}

Câu hỏi: {question}

HƯỚNG DẪN:
1. Chỉ trả lời dựa trên tài liệu được cung cấp
2. Nếu tìm thấy thông tin, trích dẫn nguồn (tên tài liệu và trang)
3. Nếu không tìm thấy, nói rõ là không có thông tin
4. BẮT BUỘC: TRẢ LỜI BẰNG TIẾNG VIỆT
5. Giữ câu trả lời rõ ràng và súc tích

Câu trả lời:"""

        history_section = ""
        if history_text:
            history_section = f"Lịch sử hội thoại trước đó:\n{history_text}\n"
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question", "history_section"]
        )

        try:
            formatted_prompt = prompt.format(
                context=context,
                question=query,
                history_section=history_section
            )
            
            answer = self.llm.invoke(formatted_prompt)

            if hasattr(answer, 'content'):
                answer_text = answer.content
            else:
                answer_text = str(answer)
            
            return {
                'answer': answer_text.strip(),
                'sources': sources
            }
        
        except Exception as e:
            print(f"Error generating answer: {e}")
            return {
                'answer': f"Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời: {str(e)}",
                'sources': sources
            }