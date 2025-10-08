import os
import sys
from pathlib  import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from langchain_astradb import AstraDBVectorStore
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever
from utils.config_loader import load_config
from utils.model_loader import ModelLoader
from typing import List
from langchain_core.documents import Document
from dotenv import load_dotenv


class Retriever:
    def __init__(self):

        self.config = load_config()
        self.model_loader = ModelLoader()
        self._load_env_variables()

        self.vector_store = None
        self.retriever = None

    def _load_env_variables(self):
        load_dotenv()

        required_vars = [
            "GOOGLE_API_KEY",
            "ASTRA_DB_API_ENDPOINT",
            "ASTRA_DB_APPLICATION_TOKEN",
            "ASTRA_DB_KEYSPACE",
        ]

        missing_vars = [var for var in required_vars if os.getenv(var) is None]
        if missing_vars:
            raise EnvironmentError(f"Missing environment variables: {missing_vars}")

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.db_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        self.db_application_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        self.db_keyspace = os.getenv("ASTRA_DB_KEYSPACE")

    def load_retriever(self):
        if not self.vector_store:
            collection_name = self.config["astra_db"]["collection_name"]
            self.vector_store = AstraDBVectorStore(
                embedding=self.model_loader.load_embeddings(),
                collection_name=collection_name,
                api_endpoint=self.db_api_endpoint,
                token=self.db_application_token,
                namespace=self.db_keyspace,
            )
        if not self.retriever:
            top_k = (
                self.config["retriever"]["top_k"] if "retriever" in self.config else 3
            )
            mmr_retriever = self.vector_store.as_retriever(
                search_type="mmr", search_kwargs={"k": top_k, "fetch_k": 20, "lambda_mult": 0.7, "score_threshold": 0.3}
            )
            llm = self.model_loader.load_llm()
            compressor = LLMChainExtractor.from_llm(llm)

            self.retriever = ContextualCompressionRetriever(
                base_retriever=mmr_retriever, base_compressor=compressor
            )
            
        print("Retriever loaded successfully.")
        return self.retriever

    def call_retriever(self, user_query: str) -> List[Document]:
        retriever = self.load_retriever()
        result = retriever.invoke(user_query)
        return result

if __name__ == "__main__":
    retriever = Retriever()
    retriever.load_retriever()
    query = "What are people saying about iphone 17 pro?"
    docs = retriever.call_retriever(query)
    for doc in docs:
        print(doc.page_content)
        print("-----")