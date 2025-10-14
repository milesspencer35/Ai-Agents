import chromadb
  
client = chromadb.CloudClient(
  api_key='ck-2ttjcu2DwFmXQHgtwU2f587uoUd2DT2sxJv4rLMEsQdY',
  tenant='cd2d8da5-72c1-4ece-8555-c0fb9d1e4e2a',
  database='test'
)

collection = client.get_or_create_collection(name="test")

collection.add(
    documents=["Hello world"],
    metadatas=[{"source": "test"}],
    ids=["id1"]
)

results = collection.query(
    query_texts=["Hello world"],
    n_results=1
)

print(results)