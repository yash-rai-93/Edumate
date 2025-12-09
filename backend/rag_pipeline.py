"""import os
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
"""
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

class EduMateRAG:
    def __init__(self):
        # 1. Setup Embeddings (Free & Local)
        # Yeh text ko numbers (vectors) mein convert karega
        print("Initializing Embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 2. Setup LLM (Groq - Free Tier)
        # Yeh actual answer generate karega
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
            
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.1-8b-instant"
        )

        # 3. Build the Database
        self._build_pipeline()

    def _build_pipeline(self):
        print("Loading documents from 'data/' folder...")
        
        documents = []
        data_path = "data"
        
        # Manually walk through the directory to handle different file types safely
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            print(f"Created '{data_path}' folder. Please put files there.")
            return

        for root, dirs, files in os.walk(data_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if file.endswith(".pdf"):
                        loader = PyPDFLoader(file_path)
                        documents.extend(loader.load())
                    elif file.endswith(".txt"):
                        loader = TextLoader(file_path, encoding="utf-8")
                        documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        if not documents:
            print("No documents found! Please add PDFs or TXT files to 'data' folder.")
            # Create a dummy index to prevent crash
            self.vectorstore = FAISS.from_texts(["EduMate is ready."], self.embeddings)
            self.retriever = self.vectorstore.as_retriever()
            return

        print(f"Loaded {len(documents)} document pages.")

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        final_docs = text_splitter.split_documents(documents)
        print(f"Total chunks created: {len(final_docs)}")

        # Create Vector Store (FAISS)
        print("Embedding documents (this might take a moment)...")
        self.vectorstore = FAISS.from_documents(final_docs, self.embeddings)
        self.retriever = self.vectorstore.as_retriever()
        print("RAG Pipeline Ready!")

    def ask(self, question: str, chat_history: list = None):
        if chat_history is None:
            chat_history = []

        print(f"User asked: {question}")
        
        # 1. Find relevant documents
        docs = self.retriever.invoke(question)
        context_text = "\n\n".join([d.page_content for d in docs])

        if not context_text:
            return "Sorry, I couldn't find any information about this in the school data."

        # Format history for the prompt (e.g., "User: Hi\nAI: Hello!")
        history_text = "\n".join([f"Student: {q}\nEduMate: {a}" for q, a in chat_history])

        # 2. Build the Prompt with History
        prompt = f"""
        You are EduMate, a helpful school assistant for Class 10 students.
        Use the following Context and Conversation History to answer the student's question accurately.
        
        Context:
        {context_text}
        
        Conversation History:
        {history_text}
        
        Current Question: {question}
        
        Instructions:
        - Answer in clear English.
        - Use the History to understand references (like "he", "it", "that").
        - Only use the provided Context. If the answer is not in the context, say "Information not available in school documents."
        - Keep it concise and student-friendly.
        
        Answer:
        """

        # 3. Get Answer from LLM
        response = self.llm.invoke(prompt)
        return response.content
    # ... (keep your existing __init__ and _build_pipeline methods) ...

    # --- NEW FUNCTION: QUIZ GENERATOR ---
    def generate_quiz(self, topic: str):
        # 1. Get relevant content
        docs = self.retriever.invoke(topic)
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. Prompt for Quiz
        prompt = f"""
        You are a strict teacher. Create a 3-question Multiple Choice Quiz (MCQ) for a Class 10 student about: "{topic}".
        Use only the provided context.
        
        Context:
        {context_text}
        
        Format:
        Q1. [Question]
        (a) [Option]
        (b) [Option]
        (c) [Option]
        (d) [Option]
        Answer: [Correct Option]
        
        (Repeat for 3 questions)
        """
        response = self.llm.invoke(prompt)
        return response.content

    # --- NEW FUNCTION: SUMMARIZER ---
    def get_summary(self, topic: str):
        docs = self.retriever.invoke(topic)
        context_text = "\n\n".join([d.page_content for d in docs])
        
        prompt = f"""
        Summarize the topic "{topic}" for a Class 10 student.
        Use bullet points. Keep it short and easy to revise.
        
        Context:
        {context_text}
        """
        response = self.llm.invoke(prompt)
        return response.content