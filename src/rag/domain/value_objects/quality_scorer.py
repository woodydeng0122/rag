from dataclasses import dataclass


@dataclass(frozen=True)
class QualityScorer:
    """黄金记录质量评分器 — 基于多维度计算单条记录质量分（0-1）

    评分维度：
    - 参考答案长度：20-300 字为佳，偏离扣分
    - ground_truth_chunks 数量：>3 扣分
    """

    min_answer_length: int = 20
    max_answer_length: int = 300
    max_gt_chunks: int = 3
    length_penalty: float = 0.2
    gt_chunks_penalty: float = 0.1

    def score(self, reference_answer: str, gt_chunks: list[str]) -> float:
        """计算质量分"""
        s = 1.0
        ans_len = len(reference_answer)
        if ans_len < self.min_answer_length or ans_len > self.max_answer_length:
            s -= self.length_penalty
        if len(gt_chunks) > self.max_gt_chunks:
            s -= self.gt_chunks_penalty
        return round(max(s, 0.0), 2)
