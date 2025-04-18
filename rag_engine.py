import logging
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.together import TogetherEmbedding
import config
import db
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.vector_stores.qdrant import QdrantVectorStore
import db
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.llms.together import TogetherLLM
import config
from llama_index.core import get_response_synthesizer
from qdrant_client import QdrantClient, models
from llama_index.embeddings.huggingface_optimum import OptimumEmbedding

from typing import Any, List, Union
from sentence_transformers import SentenceTransformer
from llama_index.core.embeddings import BaseEmbedding


class SentenceTransformerEmbeddings(BaseEmbedding):
    """
    Adapter for SentenceTransformer models in llama_index.

    Args:
        model_name: HuggingFace model identifier for SentenceTransformer.
        normalize_embeddings: Whether to normalize embeddings (default True).
    """

    def __init__(
        self,
        model_name: str = "ai-forever/ru-en-RoSBERTa",
        normalize_embeddings: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        # Load the SentenceTransformer model
        self._model = SentenceTransformer(model_name)
        # Use a private attribute to avoid Pydantic conflicts
        self._normalize_embeddings = normalize_embeddings

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Generate an embedding for a single query string.
        """
        embeddings = self._model.encode(
            [query], normalize_embeddings=self._normalize_embeddings
        )
        # Convert to Python list
        emb = embeddings[0]
        return emb.tolist() if hasattr(emb, "tolist") else list(emb)

    def _get_text_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text string.
        """
        embeddings = self._model.encode(
            [text], normalize_embeddings=self._normalize_embeddings
        )
        emb = embeddings[0]
        return emb.tolist() if hasattr(emb, "tolist") else list(emb)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.
        """
        embeddings = self._model.encode(
            texts, normalize_embeddings=self._normalize_embeddings
        )
        # Ensure Python native lists
        result: List[List[float]] = []
        for emb in embeddings:
            result.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))
        return result

    # Async wrappers matching llama_index signature
    async def _aget_query_embedding(self, query: str) -> List[float]:  # noqa: F821
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:  # noqa: F821
        return self._get_text_embedding(text)

    async def _aget_text_embeddings(
        self, texts: List[str]
    ) -> List[List[float]]:  # noqa: F821
        return self._get_text_embeddings(texts)


Settings.embed_model = SentenceTransformerEmbeddings()

Settings.llm = TogetherLLM(
    model=config.LLM_MODEL,
    api_key=config.TOGETHER_API_KEY,
)

DAN_USERNAME = config.DAN_USERNAME
ALEX_USERNAME = config.ALEX_USERNAME
ARTEM_USERNAME = config.ARTEM_USERNAME


class RagEngine:
    def __init__(self):
        # Инициализируем Qdrant клиент и векторное хранилище
        self.client = db.get_qdrant_client()
        if not self.client.collection_exists(config.QDRANT_COLLECTION):
            self.client.create_collection(
                collection_name=config.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=768, distance=models.Distance.COSINE
                ),
            )
        self.vector_store = QdrantVectorStore(
            client=self.client, collection_name=config.QDRANT_COLLECTION
        )
        # Создаём пустой индекс; embed_model и llm будут подхвачены из Settings
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store, embed_model=Settings.embed_model
        )

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
        # Если ничего не найдено — fallback к LLM напрямую
        if nodes:
            nodes = [i.text for i in nodes]

        prompt = f"""
Ты — бот в групповом чате трёх друзей: Дани {config.DAN_USERNAME}, Лёши {config.ALEX_USERNAME} и Тёмы {config.ARTEM_USERNAME}. Твоя задача — реагировать адекватно и в тон последнему сообщению:

- Если сообщение юмористическое, бытовое или неформальное, отвечай коротко, смешно и с сарказмом. Можешь пошутить грубовато, пошло или использовать локальные мемы.
- Если сообщение серьёзное, требующее нормального ответа или совета, отвечай серьёзно, кратко и по делу, без шуток и сарказма.

Используй память (<MEMORY>) — последние {config.N_LAST_MESSAGES} сообщений, и 3 факта (<FACTS>) из старых сообщений, если старые сообщения помогают понять текущую тему. Не цитируй их дословно.

Примеры:

Юмористическое сообщение:
Лёша: "Опять проебал ключи от дома"
Бот: "Пора уже вживлять чип, как коту."

Серьёзное сообщение:
Даня: "Ребят, подскажите хороший фильм на вечер"
Бот: "Посмотри 'Исчезнувшую', если хочешь триллер, от которого не оторвёшься."

История чата:
<MEMORY>{chr(10).join(history)}</MEMORY>

Теперь ответь на последнее сообщение от {from_username}: "{query_text}".

Дополнительный контекст:
<FACTS>{chr(10).join(nodes)}</FACTS>
"""
        logging.info(f"{prompt}\n\n")
        llm_response = Settings.llm.complete(prompt)

        return llm_response.text
