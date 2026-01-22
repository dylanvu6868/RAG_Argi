
import os
from dotenv import load_dotenv
load_dotenv()
from qdrant_client import QdrantClient

url = os.getenv("QDRANT_URL", "http://localhost:6333")
api_key = os.getenv("QDRANT_API_KEY")

print(f"Connecting to Qdrant at {url}...")
try:
    client = QdrantClient(url=url, api_key=api_key)
    collections = client.get_collections()
    print("Collections:")
    for c in collections.collections:
        print(f"- {c.name}")

    col_name = "rag_documents"
    if any(c.name == col_name for c in collections.collections):
        count = client.count(collection_name=col_name)
        print(f"\nCollection '{col_name}' has {count.count} vectors.")

        if count.count > 0:
            res = client.scroll(collection_name=col_name, limit=1, with_payload=True)
            if res[0]:
                print("\nSample Chunk Payload:")
                print(res[0][0].payload)
    else:
        print(f"\nCollection '{col_name}' NOT found yet (Process some PDFs to create it).")
        
except Exception as e:
    print(f"Error connecting to Qdrant: {e}")
