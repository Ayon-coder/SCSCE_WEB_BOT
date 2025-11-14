import os
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage

def get_index(pages, name, embed_model=None):
    """
    Creates or loads a vector index for the given PDF pages.
    Automatically uses the provided embedding model (HuggingFace, etc.).
    """
    try:
        storage_dir = f"./storage/{name}"
        os.makedirs(storage_dir, exist_ok=True)

        if os.path.exists(os.path.join(storage_dir, "docstore.json")):
            print(f"📦 Loading existing index: {name}")
            storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
            return load_index_from_storage(storage_context)

        print(f"⚙️ Creating new index for: {name}")
        index = VectorStoreIndex.from_documents(
            pages, embed_model=embed_model
        )
        
        index.storage_context.persist(persist_dir=storage_dir)
        print(f"✅ Index created and saved for: {name}")
        return index

    except Exception as e:
        print(f"❌ Error in get_index(): {e}")
        raise
