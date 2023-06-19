from typing import Optional, Any, List, cast

import weaviate
from langchain.embeddings.base import Embeddings
from langchain.schema import Document, BaseRetriever
from langchain.vectorstores import VectorStore
from pydantic import BaseModel

from core.index.base import BaseIndex
from core.index.vector_index.base import BaseVectorIndex
from core.vector_store.weaviate_vector_store import WeaviateVectorStore
from models.dataset import Dataset


class WeaviateConfig(BaseModel):
    endpoint: str
    api_key: Optional[str]
    batch_size: int = 100


class WeaviateVectorIndex(BaseVectorIndex):
    def __init__(self, dataset: Dataset, config: WeaviateConfig, embeddings: Embeddings, attributes: list[str]):
        self._dataset = dataset
        self._client = self._init_client(config)
        self._embeddings = embeddings
        self._attributes = attributes
        self._vector_store = None

    def _init_client(self, config: WeaviateConfig) -> weaviate.Client:
        auth_config = weaviate.auth.AuthApiKey(api_key=config.api_key)

        weaviate.connect.connection.has_grpc = False

        client = weaviate.Client(
            url=config.endpoint,
            auth_client_secret=auth_config,
            timeout_config=(5, 60),
            startup_period=None
        )

        client.batch.configure(
            # `batch_size` takes an `int` value to enable auto-batching
            # (`None` is used for manual batching)
            batch_size=config.batch_size,
            # dynamically update the `batch_size` based on import speed
            dynamic=True,
            # `timeout_retries` takes an `int` value to retry on time outs
            timeout_retries=3,
        )

        return client

    def get_type(self) -> str:
        return 'weaviate'

    def get_index_name(self, dataset_id: str) -> str:
        return "Vector_index_" + dataset_id.replace("-", "_") + '_Node'

    def to_index_struct(self) -> dict:
        return {
            "type": self.get_type(),
            "vector_store": {"class_prefix": self.get_index_name(self._dataset.get_id())}
        }

    def create(self, texts: list[Document]) -> BaseIndex:
        uuids = self._get_uuids(texts)
        self._vector_store = WeaviateVectorStore.from_documents(
            texts,
            self._embeddings,
            client=self._client,
            index_name=self.get_index_name(self._dataset.get_id()),
            uuids=uuids,
            by_text=False
        )

        return self

    def _get_vector_store(self) -> VectorStore:
        """Only for created index."""
        if self._vector_store:
            return self._vector_store

        return WeaviateVectorStore(
            client=self._client,
            index_name=self.get_index_name(self._dataset.get_id()),
            text_key='text',
            embedding=self._embeddings,
            attributes=self._attributes,
            by_text=False
        )

    def _get_vector_store_class(self) -> type:
        return WeaviateVectorStore

    def delete_by_document_id(self, document_id: str):
        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        vector_store.del_texts({
            "operator": "Equal",
            "path": ["document_id"],
            "valueText": document_id
        })
