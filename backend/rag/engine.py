import logging
import os

from dotenv import load_dotenv
import chromadb
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.groq import Groq
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.vector_stores.chroma import ChromaVectorStore
from rag.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger("rag.engine")

# Ucitavanje .env fajla
load_dotenv()

# 1. Inicijalizacija LLM-a
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("Greska: GROQ_API_KEY nije postavljen u .env fajlu!")

Settings.llm = Groq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
    temperature=0.5,
    max_tokens=1024,
)

# 2. Embedding model
Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

# 3. Chunking - manji chunkovi preciznije rade za IT hardver Q&A
# nego LlamaIndex podrazumevane vrednosti (1024/200).
Settings.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)


def _get_chroma_path() -> str:
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, "..", "chroma_db")


def _get_uploads_path() -> str:
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, "..", "uploads")


def create_chat_engine():
    # 4. Kreiranje ChromaDB klijenta i kolekcije
    chroma_dir = _get_chroma_path()
    os.makedirs(chroma_dir, exist_ok=True)

    db = chromadb.PersistentClient(path=chroma_dir)
    chroma_collection = db.get_or_create_collection("it_hardver_baza")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    uploads_dir = _get_uploads_path()
    os.makedirs(uploads_dir, exist_ok=True)

    # 5. KLJUCNA PROVERA: oslanjamo se na stvarno stanje vektorske baze
    # (broj embedovanih vektora), ne na to da li je uploads/ prazan.
    # Bez ovoga se pri svakom restartu duplira ceo indeks.
    existing_count = chroma_collection.count()

    if existing_count > 0:
        logger.info(
            "Kolekcija 'it_hardver_baza' vec sadrzi %d chunkova - "
            "ucitavam postojeci indeks bez ponovnog embeddovanja.",
            existing_count,
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context
        )
    elif not os.listdir(uploads_dir):
        logger.warning("'uploads' folder je prazan. Ucitavam praznu bazu!")
        index = VectorStoreIndex.from_documents([], storage_context=storage_context)
    else:
        documents = SimpleDirectoryReader(uploads_dir).load_data()
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )
        logger.info(
            "Indeksirano %d dokumenata iz uploads/ u novu kolekciju.",
            len(documents),
        )

    # 6. Konfiguracija memorije četa
    memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

    # 7. Vracanje spremnog engine-a
    return index.as_chat_engine(
        chat_mode="condense_plus_context",
        memory=memory,
        system_prompt=SYSTEM_PROMPT,
    )


# Kreiranje globalne instance koju FastAPI ruta importuje
engine = create_chat_engine()