from llm_interface import SentenceTransformerEmbeddings
import logging
from llama_index.vector_stores.qdrant import QdrantVectorStore
import config as config
import db as db
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.together import TogetherLLM
from qdrant_client import models
from llama_index.core.tools.tool_spec.load_and_search.base import LoadAndSearchToolSpec
from llama_index.tools.duckduckgo.base import DuckDuckGoSearchToolSpec
from llama_index.core.prompts import RichPromptTemplate
from prompt_templates import web_search_template, std_template

Settings.embed_model = SentenceTransformerEmbeddings()

Settings.llm = TogetherLLM(
    model=config.LLM_MODEL, api_key=config.TOGETHER_API_KEY, context_window=8000
)


class RagEngine:
    def __init__(self):
        # Инициализируем Qdrant клиент и векторное хранилище
        self.client = db.get_qdrant_client()
        self.web_search_spec = DuckDuckGoSearchToolSpec()
        if not self.client.collection_exists(config.QDRANT_COLLECTION):
            self.client.create_collection(
                collection_name=config.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=1024, distance=models.Distance.COSINE
                ),
            )
        self.vector_store = QdrantVectorStore(
            client=self.client, collection_name=config.QDRANT_COLLECTION
        )
        # Создаём пустой индекс; embed_model и llm будут подхвачены из Settings
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store, embed_model=Settings.embed_model
        )

    def search_web(self, query_text: str, from_username: str, history: list) -> str:
        query_text = query_text.replace("Загугли", "")

        results = self.web_search_spec.duckduckgo_full_search(query_text, "ru-ru")

        prompt = web_search_template.format(
            dan_username=config.DAN_USERNAME,
            alex_username=config.ALEX_USERNAME,
            artem_username=config.ARTEM_USERNAME,
            chat_history=chr(10).join(history),  # chr(10) - перенос строки
            from_username=from_username,
            query_text=query_text,
            results=results,
        )
        logging.info(f"{prompt}\n\n")
        llm_response = Settings.llm.complete(prompt)

        return llm_response.text

    def index_documents(self, docs: list):
        """
        Индексируем список документов.
        При совпадении doc_id в Qdrant будет upsert.
        """
        for doc in docs:
            self.index.insert(
                Document(text=doc["text"], doc_id=doc["id"], metadata=doc["metadata"])
            )

    def query(self, query_text: str, from_username: str, history: list) -> str:
        # Получаем retriever и делаем явный ретрив документов
        retriever = self.index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(query_text)
        if nodes:
            nodes = [i.text for i in nodes]
        else:
            nodes = ["Пока ничего не помнишь."]
        prompt = std_template.format(
            dan_username=config.DAN_USERNAME,
            alex_username=config.ALEX_USERNAME,
            artem_username=config.ARTEM_USERNAME,
            chat_history=chr(10).join(history),  # chr(10) - перенос строки
            from_username=from_username,
            query_text=query_text,
            found_nodes=chr(10).join(nodes),
        )

        logging.info(f"{prompt}\n\n")
        llm_response = Settings.llm.complete(prompt)

        return llm_response.text
