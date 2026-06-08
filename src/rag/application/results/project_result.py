from dataclasses import dataclass

from rag.domain.entities.project import Project


@dataclass
class ProjectResult:
    """项目查询结果 — 包含关联的嵌入模型名称，供 Presenter 使用"""

    project: Project
    embed_model_name: str = ""
