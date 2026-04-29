from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Iterable

from openai import OpenAI

from config import config

_client = None
_EMBEDDING_DIMENSION = 384


def _has_placeholder_key() -> bool:
    key = (config.LLM_API_KEY or "").strip()
    return not key or key.lower() in {"sk-your-api-key-here", "sk-test-placeholder"}


def _should_use_remote() -> bool:
    return not _has_placeholder_key()


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
        )
    return _client


def _extract_topic(text: str) -> str:
    patterns = [
        r"用户正在学习[:：]\s*(.+)",
        r"学习主题[:：]\s*(.+)",
        r"当前学习主题\s*\n\s*(.+)",
        r"## 当前学习主题\s*\n\s*(.+)",
        r"## 学习主题[:：]\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().splitlines()[0][:60]
    return "这个主题"


def _extract_keywords(text: str, limit: int = 4) -> list[str]:
    candidates = []
    phrases = re.findall(r"[\u4e00-\u9fffA-Za-z0-9=+\-()/·]{2,}", text)
    for phrase in phrases:
        cleaned = phrase.strip()
        if len(cleaned) < 2:
            continue
        if cleaned in candidates:
            continue
        if cleaned in {"JSON", "markdown", "markdown格式"}:
            continue
        candidates.append(cleaned)
        if len(candidates) >= limit:
            break
    return candidates


def _local_teacher_reply(text: str) -> str:
    topic = _extract_topic(text)
    keywords = _extract_keywords(text)
    focus = f"，先抓住{keywords[0]}" if keywords else ""
    return (
        f"我们先把{topic}想成一个容易理解的生活例子。"
        f"如果你愿意，可以先用自己的话描述你对它的理解{focus}，"
        f"我再帮你一点点补齐。"
    )


def _local_validator_reply(text: str) -> str:
    topic = _extract_topic(text)
    keywords = _extract_keywords(text)
    target = keywords[0] if keywords else topic
    return f"我不太明白{target}为什么会这样。那如果换一个场景，结论还成立吗？"


def _local_welcome_reply(text: str) -> str:
    topic = _extract_topic(text)
    keywords = _extract_keywords(text)
    if keywords:
        reminder = f"比如 {keywords[0]} 和 {keywords[1]}" if len(keywords) > 1 else f"比如 {keywords[0]}"
        return f"欢迎回来！上次你在{topic}上已经走到这一步了，{reminder} 可以先复习一下。"
    return f"欢迎回来！今天可以继续巩固 {topic}，先把基础概念过一遍会更稳。"


def _local_memory_json(text: str) -> str:
    topic = _extract_topic(text)
    keywords = _extract_keywords(text, limit=6)
    weak_points: list[str] = []
    strengths: list[str] = []

    lower_text = text.lower()
    if any(token in lower_text for token in ["不懂", "不太明白", "混淆", "困惑", "不会", "搞不清"]):
        weak_points.extend(keywords[:2] or [topic])
    else:
        strengths.extend(keywords[:2])

    if not weak_points and keywords:
        weak_points = [keywords[0]] if len(keywords) == 1 else keywords[:2]

    if not strengths and keywords:
        strengths = keywords[:2]

    summary = f"围绕{topic}完成了一次基础讲解"
    if keywords:
        summary = f"围绕{topic}讨论了{keywords[0]}等关键点"

    level = "beginner"
    if any(token in lower_text for token in ["掌握", "理解", "明白", "会了"]):
        level = "intermediate"
    if any(token in lower_text for token in ["熟练", "非常清楚", "已经会"]):
        level = "advanced"

    payload = {
        "weak_points": weak_points[:3],
        "strengths": strengths[:3],
        "summary": summary,
        "review_priority": weak_points[:3] or keywords[:2],
        "understanding_level": level,
    }
    return json.dumps(payload, ensure_ascii=False)


def _local_chat(messages: list[dict]) -> str:
    prompt_text = "\n".join(str(message.get("content", "")) for message in messages)
    if "只返回JSON" in prompt_text or "JSON格式" in prompt_text:
        return _local_memory_json(prompt_text)
    if "欢迎回来" in prompt_text or "复习" in prompt_text:
        return _local_welcome_reply(prompt_text)
    if "学生" in prompt_text and ("提问" in prompt_text or "疑问" in prompt_text):
        return _local_validator_reply(prompt_text)
    return _local_teacher_reply(prompt_text)


def chat(messages: list[dict], temperature: float = 0.7) -> str:
    if _should_use_remote():
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception:
            pass
    return _local_chat(messages)


def _hash_to_float(token: str) -> float:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    value = int.from_bytes(digest[:4], "big") / 2**32
    return value * 2.0 - 1.0


def _local_embedding(text: str) -> list[float]:
    vector = [0.0] * _EMBEDDING_DIMENSION
    if not text:
        return vector

    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9=+\-()/·]{1,}", text)
    if not tokens:
        tokens = list(text)

    for token in tokens:
        index = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % _EMBEDDING_DIMENSION
        vector[index] += 1.0
        vector[(index + 97) % _EMBEDDING_DIMENSION] += _hash_to_float(token) * 0.25

    norm = math.sqrt(sum(value * value for value in vector))
    if norm > 0:
        vector = [value / norm for value in vector]
    return vector


def get_embedding(text: str) -> list[float]:
    if _should_use_remote():
        try:
            client = get_client()
            response = client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception:
            pass
    return _local_embedding(text)


class EmbeddingFunctionAdapter:
    def name(self) -> str:
        return "chemind-learn-embedding-adapter"

    def _embed_many(self, inputs: Iterable[str]) -> list[list[float]]:
        return [get_embedding(text) for text in inputs]

    def __call__(self, input):
        if isinstance(input, str):
            return self._embed_many([input])
        return self._embed_many(list(input))

    def embed_query(self, input):
        if isinstance(input, str):
            return get_embedding(input)
        return self._embed_many(list(input))


def get_embedding_function():
    return EmbeddingFunctionAdapter()