"""诊断：验证新的 tokenize 函数是否解决了英文词问题"""
import re
import jieba


def _extract_english_words(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z]{2,}", text)
    seen = set()
    result = []
    for w in words:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw)
            result.append(lw)
    return result


def _tokenize_new(text: str) -> str:
    english_words = _extract_english_words(text)
    chinese_tokens = [t for t in jieba.cut(text) if t.strip() and not re.match(r"^[A-Za-z]{2,}$", t)]
    all_tokens = english_words + chinese_tokens
    return " ".join(all_tokens)


def _build_or_tsquery_new(text: str) -> str:
    english_words = _extract_english_words(text)
    chinese_tokens = jieba.cut(text)
    chinese_terms = [
        t.strip() for t in chinese_tokens
        if t.strip() and len(t.strip()) > 1 and not re.match(r"^[A-Za-z]{2,}$", t)
    ]
    all_terms = english_words + chinese_terms
    if not all_terms:
        all_terms = [t.strip() for t in jieba.cut(text) if t.strip()]
    return " | ".join(all_terms)


# 模拟之前诊断中发现的典型 chunk 和 query
test_cases = [
    {
        "name": "chunk_2 (## 功能 - Path Op)",
        "content": "## 功能 { #features }\n\n - * * Path Op\n\n官方 的 FastAPI 扩展",
        "query": "FastAPI 扩展提供了哪些方式来发现和导航到应用中的路径操作？",
    },
    {
        "name": "chunk_0 (# 编辑器支持)",
        "content": "# 编辑器支持 { #editor-support }\n\n官方 的 FastAPI VS Code 扩展",
        "query": "如何在 VS Code 或 Cursor 中安装 FastAPI 扩展？它提供了哪些主要功能？",
    },
]

print("=== 旧 tokenize vs 新 tokenize ===\n")
for tc in test_cases:
    print(f"[{tc['name']}]")
    print(f"  content: {tc['content'][:80]}")
    print(f"  query:   {tc['query'][:60]}")

    old_tokens = " ".join(jieba.cut(tc["content"]))
    new_tokens = _tokenize_new(tc["content"])
    old_query = " ".join(jieba.cut(tc["query"]))
    new_query = _build_or_tsquery_new(tc["query"])

    print(f"  旧 tokens: {old_tokens[:80]}")
    print(f"  新 tokens: {new_tokens[:80]}")
    print(f"  旧 query:  {old_query[:80]}")
    print(f"  新 query:  {new_query[:80]}")

    # 检查新 tokens 是否能匹配新 query
    query_terms = set(new_query.split(" | "))
    chunk_terms = set(new_tokens.split())
    overlap = query_terms & chunk_terms
    print(f"  新 overlap: {overlap}")
    print()
