from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LearningRecord(BaseModel):
    id: str
    topic: str
    user_understanding: str
    weak_points: list[str]
    timestamp: str = ""
    session_summary: str = ""

    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


class QuizQuestion(BaseModel):
    question: str
    expected_concepts: list[str]
    difficulty: str = "medium"


class SessionState(BaseModel):
    topic: str
    phase: str = "teaching"  # teaching / quizzing / review
    history: list[dict] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    understanding_level: str = "beginner"


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    topic: str
    message: str = ""


class ChatResponse(BaseModel):
    session_id: str
    phase: str
    content: str
    weak_points: list[str] = Field(default_factory=list)