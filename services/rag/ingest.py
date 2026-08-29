import os
import glob
from dotenv import load_dotenv

# Dynamically add Tesseract to PATH (default installation location from winget)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Tesseract-OCR"

from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def get_vision_llm():
    """Returns a vision-capable LLM via OpenRouter."""
    return ChatOpenAI(
        # meta-llama/llama-3.2-11b-vision-instruct:free is a free vision model on OpenRouter
        model="meta-llama/llama-3.2-11b-vision-instruct:free",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

def summarize_image(chunk):
    """Uses a vision-capable LLM to describe an image extracted from a PDF.
    
    Images in PDFs are raw pixel data (charts, maps, diagrams). They have
    NO extractable text. We send the base64 image to a vision LLM which
    reads the pixels and returns a text description we can embed and search.
    """
    base64_image = getattr(chunk.metadata, 'image_base64', None) if hasattr(chunk, 'metadata') else None
    
    if not base64_image:
        print("    [Image] No base64 data found, skipping.")
        return "Image element with no extractable content."
    
    try:
        llm = get_vision_llm()
        msg = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "You are analyzing an image extracted from an official Indian flood management "
                        "or disaster response PDF document. Describe this image in detail so it can be "
                        "retrieved via semantic search. Focus on: what type of visual it is (map, chart, "
                        "diagram, table, photo), what data or information it shows, any visible labels, "
                        "legends, titles, or annotations, and what flood/disaster management context it relates to."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        )
        response = llm.invoke([msg])
        print("    [Image] Vision summary generated.")
        return response.content
    except Exception as e:
        print(f"    [Image] Vision LLM failed ({e}), falling back to empty description.")
        return "Image element — vision summarization failed."

def summarize_table(chunk):
    """Returns raw extracted HTML text for Table elements.
    Tables already have their text extracted by unstructured's parser,
    so we just use that directly without an LLM call.
    """
    if hasattr(chunk.metadata, 'text_as_html') and chunk.metadata.text_as_html:
        return chunk.metadata.text_as_html
    return chunk.text if hasattr(chunk, 'text') else str(chunk)

def partition_document(file_path: str):
    print(f"Partitioning document: {file_path}")
    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image"],
        extract_image_block_to_payload=True
    )
    print(f"Extracted {len(elements)} elements")
    return elements

def create_chunks_by_title(elements):
    print("Creating smart chunks...")
    chunks = chunk_by_title(
        elements,
        max_characters=3000,
        new_after_n_chars=2400,
        combine_text_under_n_chars=500
    )
    print(f"Created {len(chunks)} chunks")
    return chunks

def ingest_documents():
    data_dir = r"d:\FloodGuard\datasets\rag"
    persist_dir = r"d:\FloodGuard\rag\chroma_db"
    
    pdf_files = glob.glob(os.path.join(data_dir, "**", "*.pdf"), recursive=True)
    
    if not pdf_files:
        print(f"No PDFs found in {data_dir}")
        return

    all_langchain_docs = []
    
    for pdf_path in pdf_files:
        elements = partition_document(pdf_path)
        chunks = create_chunks_by_title(elements)
        
        # Convert Unstructured chunks to Langchain Documents
        print(f"Converting {len(chunks)} chunks to Langchain Documents for {os.path.basename(pdf_path)}...")
        for i, chunk in enumerate(chunks):
            category = getattr(chunk, 'category', 'Text')
            
            # Route each chunk to the appropriate processor
            if category == 'Image':
                print(f"  [{i+1}/{len(chunks)}] Processing Image (vision LLM)...")
                page_content = summarize_image(chunk)
            elif category == 'Table':
                print(f"  [{i+1}/{len(chunks)}] Processing Table (raw HTML text)...")
                page_content = summarize_table(chunk)
            else:
                if i % 10 == 0:
                    print(f"  [{i+1}/{len(chunks)}] Processing Text chunks...")
                page_content = str(chunk)
                
            raw_metadata = chunk.metadata.to_dict() if hasattr(chunk, 'metadata') else {}
            metadata = {'chunk_category': category}
            
            # Store original HTML or base64 in metadata for retrieval later
            if category == 'Table' and hasattr(chunk.metadata, 'text_as_html'):
                metadata['original_table_html'] = chunk.metadata.text_as_html
                
            # Sanitize metadata for ChromaDB (only allows str, int, float, bool)
            for key, value in raw_metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
                elif value is not None:
                    metadata[key] = str(value)
                
            doc = Document(
                page_content=page_content,
                metadata=metadata
            )
            all_langchain_docs.append(doc)

    print(f"Total Langchain chunks loaded: {len(all_langchain_docs)}")
    print("Generating HuggingFace embeddings and storing in ChromaDB...")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    db = Chroma.from_documents(
        documents=all_langchain_docs,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    print("Ingestion complete. ChromaDB saved to", persist_dir)

if __name__ == "__main__":
    ingest_documents()
