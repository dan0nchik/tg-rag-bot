from typing import Any, List
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
