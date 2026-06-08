"""黄金数据集生成的 Prompt 模板"""


def whole_doc_question_prompt(
    full_doc: str,
    chunks_info: str,
    n_questions: int,
    type_dist: str,
    user_persona: str,
) -> str:
    """整篇文档模式：一次 LLM 调用生成所有问题"""
    return (
        "你是 RAG 评测数据生成专家。仔细阅读以下完整文档，\n",
        f"生成 {n_questions} 个真实用户可能提出的问题。\n\n",
        "规则：\n",
        "- 不要考虑文档如何被切分，只关注文档传达的知识点\n",
        f"- 风格贴近真实用户提问（{user_persona}）\n",
        f"- 覆盖不同类型：{type_dist}\n",
        "- 不要直接复制原文句子作为问题\n",
        "- difficulty 按\u201c检索难度\u201d标注：\n",
        "  - easy：query 关键词与原文高度重叠\n",
        "  - medium：query 用词与原文有差异\n",
        "  - hard：query 需要推理/跨段综合\n",
        "- 对于 comparison 类型，问题需要对比文档中不同部分的内容\n",
        "- 对于 unanswerable 类型，生成看起来相关但文档无法回答的问题\n\n",
        f"文档：\n{full_doc}\n\n",
        f"文档分块信息（用于映射）：\n{chunks_info}\n\n",
        "输出格式（JSON 数组）：\n",
        '[{"query": "...", "type": "factual|procedural|reasoning|comparison|unanswerable", ',
        '"difficulty": "easy|medium|hard", "answerable": true|false, ',
        '"ground_truth_chunks": ["chunk_id_1"]}]'
    )


def chunk_batch_question_prompt(
    chunks_text: str,
    n_questions: int,
    type_dist: str,
    user_persona: str,
) -> str:
    """分批 chunk 模式：生成问题"""
    return (
        "你是 RAG 评测数据生成专家。阅读以下文本片段，\n",
        f"生成 {n_questions} 个真实用户可能提出的问题。\n\n",
        "规则：\n",
        f"- 风格贴近真实用户提问（{user_persona}）\n",
        f"- 覆盖不同类型：{type_dist}\n",
        "- 不要直接复制原文句子作为问题\n",
        "- difficulty 按\u201c检索难度\u201d标注\n",
        "- 对于 unanswerable 类型，生成与片段主题相关但片段无法回答的问题\n\n",
        f"文本片段：\n{chunks_text}\n\n",
        "输出格式（JSON 数组）：\n",
        '[{"query": "...", "type": "factual|procedural|reasoning|comparison|unanswerable", ',
        '"difficulty": "easy|medium|hard", "answerable": true|false}]'
    )


def answer_generation_prompt(
    chunks_text: str,
    query: str,
) -> str:
    """Phase 2：根据文本片段生成参考答案"""
    return (
        "根据以下文本片段，回答问题。\n\n",
        "规则：\n",
        "- 答案完全基于给定文本，不引入外部知识\n",
        "- 简洁准确，20-300 字\n",
        "- 如果文本中没有答案，回答\u201c该问题在文档中无对应信息\u201d\n\n",
        f"文本片段：\n{chunks_text}\n\n",
        f"问题：{query}\n\n",
        '输出格式（JSON）：\n{"reference_answer": "...", "supporting_quotes": ["原文片段1"]}'
    )
