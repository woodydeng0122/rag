from dataclasses import dataclass


@dataclass
class EvaluateResult:
    """评测结果 — 用例的输出，纯业务数据"""
    answerable_count: int
    recall: dict
    mrr: float
    failure: list[str]
    # 运行时元数据
    time: str = ""
    latency_total_ms: float = 0.0
    latency_avg_ms: float = 0.0
