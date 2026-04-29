from memory.vector_store import VectorStore
from utils.llm_client import chat
from agents.memory_agent import build_memory_analysis_prompt, build_review_reminder_prompt
import json


class MemorySystem:
    def __init__(self, embedding_function=None):
        self.store = VectorStore(embedding_function=embedding_function)

    def analyze_and_store(self, topic: str, conversation_text: str) -> dict:
        prompt = build_memory_analysis_prompt(topic, conversation_text)
        raw = chat([{"role": "user", "content": prompt}], temperature=0.3)
        try:
            raw_clean = raw.strip()
            if raw_clean.startswith("```"):
                lines = raw_clean.split("\n")
                raw_clean = "\n".join(lines[1:-1])
            analysis = json.loads(raw_clean)
        except json.JSONDecodeError:
            analysis = {
                "weak_points": [],
                "strengths": [],
                "summary": "分析失败",
                "review_priority": [],
                "understanding_level": "beginner",
            }

        record = {
            "topic": topic,
            "weak_points": analysis.get("weak_points", []),
            "strengths": analysis.get("strengths", []),
            "summary": analysis.get("summary", ""),
            "review_priority": analysis.get("review_priority", []),
            "understanding_level": analysis.get("understanding_level", "beginner"),
        }
        record_id = self.store.add_record(record)
        record["id"] = record_id
        return record

    def get_context_for_topic(self, topic: str) -> str:
        weak_points = self.store.get_weak_points_for_topic(topic)
        if not weak_points:
            return ""
        return f"相关薄弱知识点: {', '.join(weak_points)}"

    def generate_welcome_back(self) -> str:
        recent = self.store.get_recent_records(5)
        if not recent:
            return ""

        all_weak = []
        last_time = ""
        for r in recent:
            meta = r.get("metadata", {})
            wp = meta.get("weak_points", "[]")
            try:
                all_weak.extend(json.loads(wp))
            except (json.JSONDecodeError, TypeError):
                pass
            ts = meta.get("timestamp", "")
            if ts and (not last_time or ts > last_time):
                last_time = ts

        weak_unique = list(set(all_weak))[:5]
        if not weak_unique:
            return ""

        prompt = build_review_reminder_prompt(
            weak_records="\n".join(f"  - {w}" for w in weak_unique),
            last_study_time=last_time[:10] if last_time else "首次使用",
        )
        return chat([{"role": "user", "content": prompt}], temperature=0.7)

    def search_history(self, query: str, n: int = 5) -> list[dict]:
        return self.store.search_similar(query, n_results=n)