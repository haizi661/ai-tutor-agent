import os
import glob
import shutil
from typing import List
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pypdf import PdfReader

from ..core.ports import KnowledgeProvider
from ..config import Settings

class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key
        )
        self.vector_store = InMemoryVectorStore(self.embeddings)
        self._load_documents()

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
                print(f"✅ 已加载: {os.path.basename(file_path)}")

        if documents:
            self.vector_store.add_documents(documents)

    def add_document(self, source_path: str) -> bool:
        """动态复制并加载外部文件到知识库"""
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
                self.vector_store.add_documents(docs)
                print(f"🎉 成功上传并解析: {filename} (已保存至 {dest_path})")
                return True
            else:
                print(f"⚠️ 文件内容为空或无法解析: {filename}")
                return False
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False

    def query(self, query: str) -> str:
        if not self.vector_store:
            return ""
        
        results = self.vector_store.similarity_search(query, k=3)
        if not results:
            return ""
        
        context = "\n---\n".join([doc.page_content for doc in results])
        return context

