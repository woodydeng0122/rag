from dataclasses import dataclass, field


DEFAULT_QUESTION_TYPES: dict[str, float] = {
    "factual": 0.4,
    "procedural": 0.25,
    "reasoning": 0.15,
    "comparison": 0.1,
    "unanswerable": 0.1,
}


@dataclass
class GenerateConfig:
    """LLM 生成黄金数据的配置"""

    per_chunk: int = 2
    question_types: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_QUESTION_TYPES))
    difficulty: str = "mixed"
    user_persona: str = "开发者"
    chunk_batch_size: int = 3
    file_char_threshold: int = 5000

    def to_dict(self) -> dict:
        return {
            "per_chunk": self.per_chunk,
            "question_types": self.question_types,
            "difficulty": self.difficulty,
            "user_persona": self.user_persona,
            "chunk_batch_size": self.chunk_batch_size,
            "file_char_threshold": self.file_char_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerateConfig":
        return cls(
            per_chunk=data.get("per_chunk", 2),
            question_types=data.get("question_types", dict(DEFAULT_QUESTION_TYPES)),
            difficulty=data.get("difficulty", "mixed"),
            user_persona=data.get("user_persona", "开发者"),
            chunk_batch_size=data.get("chunk_batch_size", 3),
            file_char_threshold=data.get("file_char_threshold", 5000),
        )
