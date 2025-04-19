from qdrant_client import QdrantClient
import os

import config as config


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host="localhost",
        api_key=config.QDRANT_API_KEY,
        port=6333,
        https=False,
    )
