import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv(override=True)

def main():
    persist_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
    
    if not os.path.exists(persist_dir):
        print("Vector database not found. Please run ingest.py first.")
        return

    # Use free local HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Loading vector database...")
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    
    # Explicitly configure for OpenRouter
    llm = ChatOpenAI(
        model="tencent/hy3:free", 
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    print("\nRAG System Ready! Type 'exit' or 'quit' to stop.")
    
    while True:
        query = input("\nAsk a question about the Flood Guidelines: ")
        if query.lower() in ['exit', 'quit']:
            break
            
        print("\nSearching documents...")
        # Retrieve top 4 most similar chunks
        docs = db.similarity_search(query, k=4)
        
        # Combine the chunks into a single context string
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        
        # Build the final prompt
        prompt = f"""You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Keep the answer concise and clearly formatted.

Context:
{context}

Question:
{query}

Answer:"""

        print("Generating answer...\n")
        response = llm.invoke(prompt)
        print("-" * 50)
        print(response.content)
        print("-" * 50)

if __name__ == "__main__":
    main()
