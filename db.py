from qdrant_client import QdrantClient
import os


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host="host.docker.internal", port=6333)
