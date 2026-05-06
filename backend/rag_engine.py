import os
import time
from typing import List
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
import openai


class RAGEngine:
    def __init__(self):
        # Using local embeddings for independence from OpenAI
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            openai_api_key=os.getenv("GROQ_API_KEY"),
            openai_api_base="https://api.groq.com/openai/v1",
            temperature=0,
            max_tokens=1000
        )
        self.vector_db_path = "./chroma_db"
        self.vector_store = self._get_or_create_vector_store()

    def _get_or_create_vector_store(self):
        return Chroma(
            persist_directory=self.vector_db_path,
            embedding_function=self.embeddings
        )

    def ingest_document(self, file_path: str):
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        self.vector_store.add_documents(chunks)

    def query(self, question: str, chat_history: List = []):
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        # Convert raw history tuples to LangChain message objects
        lc_history = []
        for role, content in chat_history:
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            else:
                lc_history.append(AIMessage(content=content))

        # Build prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a highly professional and empathetic AI Customer Support Agent.
Use the following retrieved context to answer the customer's question.
If you don't know the answer from the context, say so honestly — do not make up an answer.
Always maintain a helpful, friendly, and professional tone.

Context:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ])

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Retrieve relevant documents — guard against empty vector store
        try:
            retrieved_docs = retriever.invoke(question)
        except Exception as e:
            print(f"[RAG] Vector store retrieval failed (possibly empty): {e}")
            retrieved_docs = []
        context_str = format_docs(retrieved_docs) if retrieved_docs else "No knowledge base documents found. Please upload FAQs or policy documents first."

        # Build chain using LCEL
        chain = prompt | self.llm | StrOutputParser()

        # Retry with exponential backoff on rate limit (429)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                answer = chain.invoke({
                    "context": context_str,
                    "chat_history": lc_history,
                    "question": question,
                })
                return {
                    "answer": answer,
                    "source_documents": [doc.page_content for doc in retrieved_docs]
                }
            except openai.RateLimitError as e:
                wait = 10 * (2 ** attempt)  # 10s → 20s → 40s
                print(f"[RAG] Rate limited (429): {e}. Retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(wait)
                else:
                    return {
                        "answer": "I'm currently experiencing high demand from the AI provider. Please wait a moment and try again.",
                        "source_documents": []
                    }
            except Exception as e:
                print(f"[RAG] Unexpected error: {type(e).__name__}: {e}")
                raise
