import os
import sys
import tempfile
import pickle
import ssl
import traceback
import certifi
from typing import List, Dict
from pdfminer.high_level import extract_text
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import httpx
from config import Config
from tcs_embeddings import TCSGenAIEmbeddings

class RAGService:
    def __init__(self):
        print("Loading TCS GenAI embedding model for Business Analysis...")
        self.embedding_model = None
        self.embeddings_available = False
        
        try:
            if Config.GENAI_API_KEY and Config.GENAI_API_KEY not in ["YOUR_KEY_HERE", ""]:
                self.embedding_model = TCSGenAIEmbeddings()
                self.embeddings_available = True
                print("[OK] TCS GenAI embedding model initialized successfully")
            else:
                print("[WARN] GenAI API key not configured")
        except Exception as e:
            print(f"[ERROR] Could not initialize TCS GenAI embeddings: {str(e)}")
            
        self.use_llm = Config.GENAI_API_KEY and Config.GENAI_API_KEY not in ["YOUR_KEY_HERE", ""]
        
        if self.use_llm:
            self.client = httpx.Client(verify=False)
            self.llm = ChatOpenAI(
                base_url=Config.GENAI_BASE_URL,
                model=Config.CHAT_MODEL,
                api_key=Config.GENAI_API_KEY,
                http_client=self.client
            )
            print("[OK] ChatOpenAI client initialized")
        else:
            self.llm = None
            self.client = None
            
        self.persist_directory = "./data/faiss_business_docs"
        os.makedirs(self.persist_directory, exist_ok=True)
        self.vectordb_path = os.path.join(self.persist_directory, "vectordb.faiss")
        
        self.vectordb = None
        if self.embeddings_available:
            try:
                if os.path.exists(self.vectordb_path):
                    self.vectordb = FAISS.load_local(
                        self.persist_directory,
                        self.embedding_model,
                        "vectordb",
                        allow_dangerous_deserialization=True
                    )
                    print("[OK] Loaded existing FAISS vector store")
                else:
                    print("No existing vector store found")
            except Exception as e:
                self.vectordb = None
                print(f"Could not load vector store: {e}")
                
    def upload_document(self, file_content: bytes, filename: str) -> Dict:
        """Upload and index PDF or TXT document using TCS GenAI embeddings"""
        if not self.embeddings_available:
            return {
                "success": False,
                "message": "Embedding model not available. Please check GenAI API key configuration.",
                "chunks_indexed": 0
            }
            
        try:
            raw_text = ""
            if filename.lower().endswith('.pdf'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                print(f"Extracting text from PDF {filename}...")
                raw_text = extract_text(temp_file_path)
                os.unlink(temp_file_path)
            else:
                print(f"Reading text from TXT {filename}...")
                raw_text = file_content.decode('utf-8', errors='ignore')
                
            if not raw_text or len(raw_text.strip()) < 50:
                return {
                    "success": False,
                    "message": "Could not extract meaningful text from document",
                    "chunks_indexed": 0
                }
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(raw_text)
            print(f"Split {filename} into {len(chunks)} chunks")
            
            metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]
            
            if self.vectordb is None:
                print("Creating new FAISS vector store...")
                self.vectordb = FAISS.from_texts(
                    chunks,
                    self.embedding_model,
                    metadatas=metadatas
                )
            else:
                print("Adding chunks to existing vector store...")
                self.vectordb.add_texts(chunks, metadatas=metadatas)
                
            self.vectordb.save_local(self.persist_directory, "vectordb")
            print("Vector store saved successfully.")
            
            return {
                "success": True,
                "message": f"Successfully indexed {filename}",
                "chunks_indexed": len(chunks),
                "filename": filename
            }
        except Exception as e:
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "chunks_indexed": 0
            }

    def analyze_image(self, image_base64: str, prompt: str) -> str:
        """Call GPT-4o vision with base64 image directly"""
        if not self.use_llm:
            return "Vision analysis is disabled (API key not configured)."
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            url = f"{Config.GENAI_BASE_URL.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {Config.GENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": Config.CHAT_MODEL,
                "messages": messages,
                "temperature": 0.3
            }
            
            response = self.client.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error from Vision API (Status {response.status_code}): {response.text}"
                
        except Exception as e:
            traceback.print_exc()
            return f"Error in image analysis: {str(e)}"

    def generate_impact_summary(self) -> str:
        """Generate highly-structured business impact analysis report from FAISS docs"""
        if not self.use_llm or self.vectordb is None:
            return "No documents indexed. Please upload business specifications or requirements first."
            
        try:
            retriever = self.vectordb.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 15}
            )
            query = "business requirements system processes process change specifications risks impact"
            docs = retriever.get_relevant_documents(query)
            
            context = "\n\n".join([d.page_content for d in docs])
            
            prompt = f"""
            You are a senior Business Analyst. Based on the following business requirements, change requests, 
            stakeholder feedback, and system specifications, generate a highly-structured, comprehensive 
            Business Impact Analysis Report.
            
            Context from uploaded documents:
            ---
            {context}
            ---
            
            Please structure the output exactly with the following sections (use markdown headers):
            
            # Executive Summary
            (Provide a clear, high-level summary of the proposed changes, goals, and business context.)
            
            # Proposed Changes
            (List and detail each specific system or process change requested in the documents.)
            
            # System & Process Impact
            (Analyze which systems, integrations, databases, or workflows will be impacted by the changes.)
            
            # Stakeholder & Risk Matrix
            (Identify key stakeholders affected, potential risks of implementing or not implementing the changes, and suggested mitigations.)
            
            Provide deep, analytical, and professional insights. Keep it highly detailed.
            """
            
            messages = [
                {"role": "system", "content": "You are a senior Business Analyst expert in systems engineering and change management."},
                {"role": "user", "content": prompt}
            ]
            
            url = f"{Config.GENAI_BASE_URL.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {Config.GENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": Config.CHAT_MODEL,
                "messages": messages,
                "temperature": 0.5
            }
            
            response = self.client.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error generating summary (Status {response.status_code}): {response.text}"
                
        except Exception as e:
            traceback.print_exc()
            return f"Error generating impact summary: {str(e)}"

    def chat_with_docs(self, query: str, image_base64: str = None) -> str:
        """Handle chat queries with RAG context or OCR/Vision if image is provided"""
        if not self.use_llm:
            return "AI service is disabled (API key not configured)."
            
        if image_base64:
            prompt = f"Analyze this image in the context of the business analysis. Query: {query or 'Describe this image.'}"
            return self.analyze_image(image_base64, prompt)
            
        if self.vectordb is None:
            try:
                messages = [
                    {"role": "system", "content": "You are a senior Business Analyst assistant."},
                    {"role": "user", "content": query}
                ]
                url = f"{Config.GENAI_BASE_URL.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {Config.GENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": Config.CHAT_MODEL,
                    "messages": messages,
                    "temperature": 0.5
                }
                response = self.client.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                return f"Error: {response.text}"
            except Exception as e:
                return f"Error: {str(e)}"
                
        try:
            retriever = self.vectordb.as_retriever(search_kwargs={"k": 5})
            rag_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=retriever,
                return_source_documents=True
            )
            result = rag_chain.invoke(query)
            if isinstance(result, dict):
                answer = result.get("result", "")
                sources = result.get("source_documents", [])
                source_names = list(set([doc.metadata.get("source", "Unknown") for doc in sources]))
                if source_names:
                    answer += f"\n\n*Sources referenced: {', '.join(source_names)}*"
                return answer
            return str(result)
        except Exception as e:
            traceback.print_exc()
            return f"Error in RAG chat: {str(e)}"

    def get_documents(self) -> Dict:
        """Get list of uploaded document names and total chunk count"""
        if self.vectordb is None:
            return {"sources": [], "total_chunks": 0}
        
        sources = set()
        for doc in self.vectordb.docstore._dict.values():
            if doc.metadata and "source" in doc.metadata:
                sources.add(doc.metadata["source"])
                
        return {
            "sources": list(sources),
            "total_chunks": len(self.vectordb.docstore._dict)
        }

    def clear_documents(self) -> bool:
        """Clear the vector database and remove persisted files"""
        self.vectordb = None
        import shutil
        if os.path.exists(self.persist_directory):
            try:
                shutil.rmtree(self.persist_directory)
                os.makedirs(self.persist_directory, exist_ok=True)
                return True
            except Exception as e:
                print(f"Error clearing vector store: {e}")
                return False
        return True
