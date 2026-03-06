import os
import glob
import shutil
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from pypdf import PdfReader

from ..core.ports import KnowledgeProvider
from ..config import Settings

class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.vector_store = None
        
        try:
            # 采用【混合架构】：对话用云端，Embedding 向量化强制走本地模型，规避一切网络和接口限制
            from langchain_huggingface import HuggingFaceEmbeddings
            
            print("🚀 正在加载本地知识检索引擎 (Sentence-Transformers)...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
                
            self.vector_store = InMemoryVectorStore(self.embeddings)
            self._load_documents()
            
        except Exception as e:
            print(f"⚠️ 本地知识库引擎加载失败: {e}")
            print("   系统将回退到无 RAG 模式运行。")

    def _parse_file(self, file_path: str) -> List[Document]:
        documents = []
        try:
            content = ""
            if file_path.lower().endswith(".pdf"):
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            
            if content.strip():
                documents.append(Document(
                    page_content=content, 
                    metadata={"source": file_path}
                ))
        except Exception as e:
            print(f"❌ 解析文件失败 {file_path}: {e}")
        return documents

    def _load_documents(self):
        if not self.vector_store:
            return

        knowledge_dir = self.settings.knowledge_dir
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir, exist_ok=True)
            return

        extensions = ["**/*.txt", "**/*.md", "**/*.pdf"]
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(knowledge_dir, ext), recursive=True))

        documents = []
        for file_path in files:
            docs = self._parse_file(file_path)
            if docs:
                documents.extend(docs)
                print(f"✅ 已提取文件内容: {os.path.basename(file_path)}")

        if documents:
            try:
                print(f"⏳ 正在为 {len(documents)} 个文档建立本地向量索引，请稍候...")
                self.vector_store.add_documents(documents)
                print(f"✨ 成功建立本地向量索引，知识库就绪！")
            except Exception as e:
                print(f"⚠️ 无法为文档建立索引: {e}")
                print("   RAG 功能暂时不可用，但你依然可以进行普通对话。")

    def add_document(self, source_path: str) -> bool:
        """动态复制并加载外部文件到知识库"""
        if not self.vector_store:
            print("⚠️ 向量引擎未就绪，无法上传文档。")
            return False

        if not os.path.exists(source_path):
            print(f"❌ 找不到文件: {source_path}")
            return False

        knowledge_dir = self.settings.knowledge_dir
        os.makedirs(knowledge_dir, exist_ok=True)
        
        filename = os.path.basename(source_path)
        dest_path = os.path.join(knowledge_dir, filename)

        try:
            shutil.copy2(source_path, dest_path)
            docs = self._parse_file(dest_path)
            if docs:
                print(f"⏳ 正在处理新文档并建立索引...")
                self.vector_store.add_documents(docs)
                print(f"🎉 成功导入知识库: {filename}")
                return True
            else:
                print(f"⚠️ 文件内容为空: {filename}")
                return False
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False

    def query(self, query: str) -> str:
        if not self.vector_store:
            return ""
        
        try:
            results = self.vector_store.similarity_search(query, k=3)
            if not results:
                return ""
            context = "\n---\n".join([doc.page_content for doc in results])
            return context
        except Exception as e:
            print(f"⚠️ 知识检索失败: {e}")
            return ""
