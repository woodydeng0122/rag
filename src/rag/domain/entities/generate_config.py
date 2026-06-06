from dataclasses import dataclass, field


DEFAULT_QUESTION_TYPES: dict[str, float] = {
    "factual": 0.4,
    "procedural": 0.25,
    "reasoning": 0.15,
    "comparison": 0.1,
    "unanswerable": 0.1,
}

VALID_DIFFICULTIES = {"easy", "medium", "hard", "mixed"}


@dataclass
class GenerateConfig:
    """LLM 生成黄金数据的配置"""

    per_chunk: int = 2
    question_types: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_QUESTION_TYPES))
    difficulty: str = "mixed"
    user_persona: str = "开发者"
    chunk_batch_size: int = 3
    file_char_threshold: int = 5000

    def __post_init__(self):
        if self.per_chunk < 1:
            raise ValueError("per_chunk must be >= 1")
        if self.chunk_batch_size < 1:
            raise ValueError("chunk_batch_size must be >= 1")
        if self.file_char_threshold < 0:
            raise ValueError("file_char_threshold must be >= 0")
        if self.difficulty not in VALID_DIFFICULTIES:
            raise ValueError(f"difficulty must be one of {VALID_DIFFICULTIES}")
        self._validate_question_types(self.question_types)

    @staticmethod
    def _validate_question_types(types: dict[str, float]) -> None:
        if not types:
            raise ValueError("question_types must not be empty")
        for k, v in types.items():
            if v < 0:
                raise ValueError(f"question_types['{k}'] must be >= 0, got {v}")
        total = sum(types.values())
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"question_types proportions must sum to ~1.0, got {total}")

    def estimate_total(self, chunk_count: int) -> int:
        """估算生成问题总数"""
        return chunk_count * self.per_chunk

    def format_type_distribution(self) -> str:
        """格式化问题类型分布描述"""
        parts = [f"{k} {int(v * 100)}%" for k, v in self.question_types.items()]
        return "、".join(parts)

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
        defaults = cls()
        return cls(
            per_chunk=data.get("per_chunk", defaults.per_chunk),
            question_types=data.get("question_types", defaults.question_types),
            difficulty=data.get("difficulty", defaults.difficulty),
            user_persona=data.get("user_persona", defaults.user_persona),
            chunk_batch_size=data.get("chunk_batch_size", defaults.chunk_batch_size),
            file_char_threshold=data.get("file_char_threshold", defaults.file_char_threshold),
        )
