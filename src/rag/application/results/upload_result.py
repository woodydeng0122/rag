from dataclasses import dataclass


@dataclass
class UploadResult:
    """上传结果 — 用例的输出"""
    documents: list[dict]  # 上传后创建的文档列表
    count: int = 0

    def __post_init__(self):
        self.count = len(self.documents)
