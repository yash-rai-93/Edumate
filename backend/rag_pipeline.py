import os
from dotenv import load_dotenv

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

load_dotenv()


class EduMateRAG:
    def __init__(self):

        # Load all documents from /data folder
        self.loader = DirectoryLoader(
            "data",
            glob="**/*.*",
            loader_cls=self._select_loader
        )

        # Normal splitter for TXT
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150
        )

        # Embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Groq LLaMA model
        self.llm = ChatGroq(
            groq_api_key="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",
            model="llama-3.1-8b-instant"
        )

        self._build_pipeline()

    # Loader selector for each file type
    def _select_loader(self, path):
        path = str(path).lower()

        if path.endswith(".pdf"):
            return PyPDFLoader(path)  # PDF → pages auto-split
        return TextLoader(path, encoding="utf-8")  # TXT

    def _build_pipeline(self):
        print("Loading documents...")
        docs = self.loader.load()

        print("Splitting documents...")
        final_docs = []

        for doc in docs:
            src = doc.metadata.get("source", "").lower()

            if src.endswith(".pdf"):
                # PDF → split pages using PyPDFLoader's native splitter
                pdf_loader = PyPDFLoader(src)
                pages = pdf_loader.load_and_split()
                final_docs.extend(pages)
            else:
                # TXT → recursive splitting
                chunks = self.text_splitter.split_documents([doc])
                final_docs.extend(chunks)

        print(f"Total chunks created: {len(final_docs)}")

        print("Embedding documents...")
        self.vectorstore = FAISS.from_documents(final_docs, self.embeddings)

        print("Creating retriever...")
        self.retriever = self.vectorstore.as_retriever()

        print("RAG READY!")

    def ask(self, question: str):
        # Retrieve relevant context chunks
        docs = self.retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in docs])

        # Build the prompt
        prompt = f"""
You are **EduMate** — an AI-powered school assistant designed for **Class 10 students**.  
Your purpose is to help students understand their syllabus, textbooks, notes, and school information in a simple and accurate way.

### ✔ What EduMate CAN Do  
- Answer questions from **NCERT Class 10 textbooks** (Science, Maths, SST, Hindi, English).  
- Help with **definitions, explanations, summaries, examples**, and textbook exercises (Only if the content exists in context).  
- Provide **timetable, syllabus, and exam-related information** from school documents.  
- Explain topics in **simple language suitable for a Class 10 student**.  
- Keep answers short, direct, and correct.  
- Use ONLY the knowledge given in the **context** (RAG documents).  

### ⚠ What EduMate MUST NOT Do  
- Do NOT invent facts outside the context.  
- If the answer is not present in the retrieved context, respond with:  
  **"Information is not available in the provided material."**  
- Do NOT give college-level or advanced explanations beyond Class 10 level.  
- Do NOT answer opinion-based or unrelated questions.  
- Do NOT guess missing data about school or exams.  

### ✔ Answering Style  
- Use **simple language**, suitable for a Class 10 student.  
- Use short sentences.  
- If needed, provide bullet points for clarity.  
- Stick closely to NCERT explanation style.  
- Provide examples only if they are present in the retrieved context.

### 🎯 Goal  
Help Class 10 students learn clearly, confidently, and accurately — without hallucinating or giving information not supported by the school’s learning material.

Context:
-------------------------
{context}
-------------------------

Question: {question}

Answer clearly for a Class 10 student:
"""
      # Call Groq LLM
        response = self.llm.invoke(prompt)
        return response
   
