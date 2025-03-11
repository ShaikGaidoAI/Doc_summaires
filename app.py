import streamlit as st
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import DirectoryLoader
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import getpass
import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

api_key = "AIzaSyCPfIdMffhoR2nxre5pmCFuYmvEI6G7oyY"
os.environ["GOOGLE_API_KEY"] = api_key

model_name= "gemini-1.5-flash"
llm = ChatGoogleGenerativeAI(model=model_name,temperature=0.0, google_api_key=api_key, max_tokens=None)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

rag_template = '''
Imagine you are an expert insurance advisor with deep knowledge of various insurance policies, including health, auto, life, and property insurance. Your goal is to provide clear, accurate, and user-friendly answers to customer queries based on the most relevant documents retrieved.

For each query:

Carefully analyze the retrieved documents to extract the most relevant information.
Summarize complex policy details in a way that is easy to understand.
Address any potential concerns the user might have, providing additional context if necessary.
If the retrieved information is insufficient, acknowledge the limitation and suggest general best practices.
Ensure your responses are professional, concise, and informative while maintaining a helpful and friendly tone.
Make sure you give correct answer which is relevent to the context

Use this Context to answer the Question: 
{context}
    
Question: {question}
    
Detailed Answer:
'''

def extract_tables_and_text(pdf_path):
    documents = []
    
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(doc):
            # Extract text
            text_content = page.get_text()
            
            # Extract tables
            tables = page.find_tables()
            
            # Add text as a document
            if text_content.strip():
                documents.append(Document(
                    page_content=text_content,
                    metadata={
                        'source': pdf_path,
                        'page': page_num,
                        'type': 'text'
                    }
                ))
            
            # Add tables as separate documents
            for table_index, table in enumerate(tables):
                # Convert table to markdown
                table_markdown = table.to_markdown()
                
                if table_markdown.strip():
                    documents.append(Document(
                        page_content=table_markdown,
                        metadata={
                            'source': pdf_path,
                            'page': page_num,
                            'table_index': table_index,
                            'type': 'table'
                        }
                    ))
        
        doc.close()
    
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    
    return documents

def load_pdfs_from_directory(directory_path):
    all_docs = []
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                filepath = os.path.join(root, file)
                
                # Extract documents including tables
                docs = extract_tables_and_text(filepath)
                all_docs.extend(docs)
                
                print(f"Processed: {filepath}")
    
    return all_docs

def split_documents(documents):
    final_chunks = []
    
    for doc in documents:
        if doc.metadata['type'] == 'table':
            # Keep entire table as a chunk
            final_chunks.append(Document(
                page_content=doc.page_content,
                metadata={
                    **doc.metadata,
                    'content_type': 'table'
                }
            ))
        elif doc.metadata['type'] == 'text':
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=3000,
                chunk_overlap=300,
                separators=[
                    "\n\n",  # Split on double newline first
                    "\n",    # Then on single newline
                    ". ",    # Then on periods
                    "! ",    # Then on exclamation marks
                    "? "     # Then on question marks
                ]
            )
            
            # Split text while maintaining original metadata
            text_chunks = text_splitter.split_text(doc.page_content)
            
            for chunk in text_chunks:
                if chunk.strip():
                    final_chunks.append(Document(
                        page_content=chunk.strip(),
                        metadata={
                            **doc.metadata,
                            'content_type': 'text'
                        }
                    ))
    
    
    return final_chunks

def create_rag_chain(vectorstore):
    # Retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    # Prompt Template
    prompt_template = ChatPromptTemplate.from_template(rag_template)
    
    # RAG Chain
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )
    
    return rag_chain


def initialize_directory(directory):
    # Function to handle directory selection logic
    st.session_state['selected_directory'] = directory
    st.session_state['directory_initialized'] = True
    path = f'docs\{directory}'
    documents = load_pdfs_from_directory(path)
    processed_documents = split_documents(documents)
    vectorstore = Chroma.from_documents(
        documents=processed_documents,
        embedding=embeddings,
        collection_name="pdf_documents"
    )
    rag_chain = create_rag_chain(vectorstore)
    st.session_state['rag_chain'] = rag_chain



def get_answer(directory, question,rag_chain):
    # Placeholder function logic
    response = rag_chain.invoke(question)
    return response

def main():
    st.title("Q&A Model Interface")
    
    # Get subdirectories
    base_directory = "./docs"  # Change this to your actual directory path
    directories = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]
    
    if 'directory_initialized' not in st.session_state:
        st.session_state['directory_initialized'] = False
        st.session_state['rag_chain'] = None  # Ensure it's always initialized
    
    selected_directory = st.selectbox("Select a Company", ["Select"] + directories)
    
    if selected_directory != "Select" and not st.session_state['directory_initialized']:
        initialize_directory(selected_directory)

    # Question input (Disabled until a directory is selected)
    question = st.text_input("Enter your question:", disabled=not st.session_state['directory_initialized'])
    
    # Advanced settings
    st.sidebar.header("Advanced Settings")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
    top_k = st.sidebar.slider("Top-K Sampling", 1, 50, 10)
    
    # Submit button
    if st.button("Get Answer"):
        if question and st.session_state['directory_initialized']:
            answer = get_answer(st.session_state['selected_directory'], question, st.session_state['rag_chain'])
        else:
            answer = "Please select a directory first and enter a question."
        
        st.write("### Answer:")
        st.write(answer)
    
if __name__ == "__main__":
    main()
