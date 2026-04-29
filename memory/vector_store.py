import json
import uuid
from chromadb import PersistentClient
from config import config
from utils.llm_client import get_embedding_function


class VectorStore:
    def __init__(self, embedding_function=None):
        self.client = PersistentClient(path=config.CHROMA_PERSIST_DIR)
        if embedding_function is not None:
            self.ef = embedding_function
        else:
            self.ef = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name="learning_records",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add_record(self, record: dict) -> str:
        record_id = record.get("id", str(uuid.uuid4()))
        topic = record.get("topic", "")
        weak_points = record.get("weak_points", [])
        summary = record.get("summary", "")
        strengths = record.get("strengths", [])
        review_priority = record.get("review_priority", [])

        document = f"主题: {topic}\n摘要: {summary}\n薄弱点: {', '.join(weak_points)}\n已掌握: {', '.join(strengths)}"

        metadata = {
            "topic": topic,
            "weak_points": json.dumps(weak_points, ensure_ascii=False),
            "strengths": json.dumps(strengths, ensure_ascii=False),
            "summary": summary,
            "review_priority": json.dumps(review_priority, ensure_ascii=False),
            "timestamp": record.get("timestamp", ""),
            "understanding_level": record.get("understanding_level", ""),
        }

        self.collection.add(
            ids=[record_id],
            documents=[document],
            metadatas=[metadata],
        )
        return record_id

    def search_similar(self, query: str, n_results: int = 5) -> list[dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        records = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                records.append({
                    "id": doc_id,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": metadata,
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return records

    def get_weak_points_for_topic(self, topic: str, n_results: int = 3) -> list[str]:
        results = self.search_similar(topic, n_results=n_results)
        all_weak = []
        for r in results:
            wp_str = r["metadata"].get("weak_points", "[]")
            try:
                all_weak.extend(json.loads(wp_str))
            except (json.JSONDecodeError, TypeError):
                pass
        return list(set(all_weak))

    def get_all_weak_points(self, n_results: int = 10) -> list[dict]:
        results = self.search_similar("薄弱点 理解困难 不懂 混淆", n_results=n_results)
        return [{"topic": r["metadata"].get("topic", ""), "weak_points": json.loads(r["metadata"].get("weak_points", "[]"))} for r in results if r["metadata"].get("weak_points")]

    def get_recent_records(self, n_results: int = 5) -> list[dict]:
        all_ids = self.collection.get()["ids"]
        if not all_ids:
            return []
        results = self.collection.get(ids=all_ids[-n_results:])
        return [{"id": results["ids"][i], "metadata": results["metadatas"][i] if results["metadatas"] else {}, "document": results["documents"][i] if results["documents"] else ""} for i in range(len(results["ids"]))]

    def count(self) -> int:
        return self.collection.count()