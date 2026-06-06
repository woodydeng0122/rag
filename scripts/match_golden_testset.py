"""将 golden_testset.jsonl 中的 chunk ID 映射为数据库中的实际 chunk ID"""
import json
import os

# 加载数据库中的 chunk 数据
chunks_path = os.path.join(os.path.dirname(__file__), "chunks_export.json")
with open(chunks_path, "r", encoding="utf-8") as f:
    db_chunks = json.load(f)

# 构建文件名 -> chunks 的映射（按 index 排序）
filename_to_chunks = {}
for c in db_chunks:
    fn = c["filename"]
    if fn not in filename_to_chunks:
        filename_to_chunks[fn] = []
    filename_to_chunks[fn].append(c)

# 对每个文件的 chunks 按 chunk_id 中的 index 排序
for fn in filename_to_chunks:
    filename_to_chunks[fn].sort(key=lambda c: c["chunk_id"])

# 建立 filename_stem -> filename 的映射
stem_to_filename = {}
for fn in filename_to_chunks:
    stem = fn.rsplit(".", 1)[0]  # 去掉扩展名
    stem_to_filename[stem] = fn

def resolve_stem(old_stem: str) -> str | None:
    """解析旧 stem 到实际文件名 stem

    旧格式: advanced_behind-a-proxy, tutorial_response-model, _llm-test
    新格式: behind-a-proxy, response-model, _llm-test
    """
    # 直接匹配
    if old_stem in stem_to_filename:
        return old_stem

    # 去掉前缀: advanced_, tutorial_, tutorial_security_ 等
    for prefix in ["advanced_", "tutorial_security_", "tutorial_"]:
        if old_stem.startswith(prefix):
            stripped = old_stem[len(prefix):]
            if stripped in stem_to_filename:
                return stripped

    return None

def parse_old_chunk_id(old_id: str) -> tuple[str, int]:
    """解析旧 chunk ID，返回 (filename_stem, chunk_index)"""
    parts = old_id.rsplit("_chunk_", 1)
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return old_id, -1

# 加载 golden_testset
testset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "fast-api", "golden_testset.jsonl")
with open(testset_path, "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

# 匹配逻辑
matched_count = 0
unmatched_ids = set()

for record in records:
    new_chunks = []
    for old_id in record.get("ground_truth_chunks", []):
        stem, idx = parse_old_chunk_id(old_id)
        resolved_stem = resolve_stem(stem)
        if resolved_stem:
            filename = stem_to_filename[resolved_stem]
            chunks = filename_to_chunks[filename]
            if 0 <= idx < len(chunks):
                new_chunks.append(chunks[idx]["chunk_id"])
                matched_count += 1
            else:
                unmatched_ids.add(old_id)
                print(f"  WARN: index {idx} out of range for {filename} (has {len(chunks)} chunks)")
        else:
            unmatched_ids.add(old_id)
            print(f"  WARN: no mapping for stem '{stem}' (old_id: {old_id})")
    record["ground_truth_chunks"] = new_chunks

print(f"\nMatched: {matched_count}, Unmatched: {len(unmatched_ids)}")
if unmatched_ids:
    print(f"Unmatched IDs: {unmatched_ids}")

# 过滤掉不可回答的和匹配失败的
answerable = []
for record in records:
    if record.get("ground_truth_chunks") and record.get("metadata", {}).get("answerable", True):
        answerable.append(record)

print(f"Total records: {len(records)}, Answerable with valid chunks: {len(answerable)}")

# 输出新的 JSONL（覆盖原文件）
output_path = testset_path
with open(output_path, "w", encoding="utf-8") as f:
    for record in answerable:
        out = {
            "query": record["query"],
            "ground_truth_chunks": record["ground_truth_chunks"],
            "reference_answer": record.get("reference_answer", ""),
            "metadata": record.get("metadata", {}),
        }
        if "supporting_quotes" in record:
            out["metadata"]["supporting_quotes"] = record["supporting_quotes"]
        f.write(json.dumps(out, ensure_ascii=False) + "\n")

print(f"Written to {output_path}")
