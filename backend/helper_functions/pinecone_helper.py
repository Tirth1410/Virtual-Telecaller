
import uuid
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os
load_dotenv()
os.environ["PINECONE_API"] = os.getenv("PINECONE_API")
os.environ["PINECONE_ENV"] = os.getenv("PINECONE_ENV")
os.environ["PINECONE_HOST"] = os.getenv("PINECONE_HOST")


pc = Pinecone(api_key=os.environ["PINECONE_API"])

index = pc.Index(
    host=os.environ["PINECONE_HOST"],
)

# print(f"Connected to Pinecone index: {index}")



def upload_chunks_to_pinecone(chunks , namespace):
    records = []
    for i, chunk in enumerate(chunks):
        records.append(
            {
                "_id": str(uuid.uuid4()),
                "text": chunk,  # <--- Use "text" instead of "chunk_text"
                "chunk_index": i,  # optional metadata field
            }
        )

    index.upsert_records(namespace =namespace,
                         records=records)
    
    print("Data uploaded to Pinecone for namespace:", namespace)


def get_top_k_similar(query: str, session_id: str, k: int = 3):
    """
    This function retrieves the top k similar documents from the vector database based on the query.
    """

    results = index.search(
        namespace=session_id,
        query={"inputs": {"text": query}, "top_k": k},
        fields=["text"],
    )

    hits = results.get("result", {}).get("hits", [])

    text = ""
    unique_texts = set()
    for hit in hits:
        content = hit.get("fields", {}).get("text", "").strip()
        if content and content not in unique_texts:
            text += content + "\n"
            unique_texts.add(content)

    return text





def upload_business_data_to_pinecone(business_name:str):

    namespace = business_name.replace(" ","").lower()
    loader = TextLoader("data/rag_data.txt",encoding="utf-8")
    data = loader.load()

    text = ""


    for doc in data:
        text+= doc.page_content + "\n\n"

    text_splitter= RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", " ", ".",","]
        )


    data_chunks = text_splitter.split_text(text)

    upload_chunks_to_pinecone(data_chunks, namespace)

    
