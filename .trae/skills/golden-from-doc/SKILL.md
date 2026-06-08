---
name: "golden-from-doc"
description: "Generate golden dataset entries from a local document. Invoke when user pastes a document local path, or asks to generate another golden entry for the same document."
---

# Golden From Doc

根据用户贴出的文档本地路径，生成黄金数据集条目并追加到 JSONL 文件，用户在前端手动导入。

## 触发条件

**首次触发：** 用户贴出一个文档本地路径，格式类似：

- `docs/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.md`
- `docs\<uuid>\docs\some-file.md`

路径中通常包含 UUID 段和 `docs/` 前缀，这是文档的 `storage_key`。

**续生成触发：** 用户对同一文档要求再生成一条，常见说法：

- "继续"

此时直接从 Step 2 开始，复用上下文中已有的 project_id 和分块列表，跳过 Step 1。

## 文件存储规则

| 类型 | 路径 | 说明 |
|------|------|------|
| 中间产物（脚本等） | `docs/temp/` | 不删除，保留备查 |
| 黄金数据集 | `golden/{relative_path}.jsonl` | 追加写入，前端导入 |

黄金数据集路径与源文档 `docs/` 路径一一对应：去掉源路径的 `docs/` 前缀，映射到 `golden/` 目录下，文件扩展名改为 `.jsonl`。

示例：
- 源文档 `docs/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.md` → `golden/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.jsonl`
- 源文档 `docs/fast-api/body.md` → `golden/fast-api/body.jsonl`

## 上下文管理

首次执行 Step 1 后，必须在对话上下文中记住以下信息，供续生成使用：

```
文档路径: <storage_key>
项目 ID: <project_id>
JSONL 路径: golden/<去掉 docs/ 前缀的相对路径>.jsonl
分块列表:
  - index=0, id=<chunk_id>, heading=<heading>
  - index=1, id=<chunk_id>, heading=<heading>
  - ...
```

## 执行步骤

### Step 1: 获取文档分块（仅首次执行）

运行 CLI 命令：

```bash
.venv\Scripts\python.exe -m rag list-chunks -p "<用户贴出的文档路径>"
```

从输出中提取：
- **项目 ID** — 输出中的 `项目 ID: <uuid>` 行
- **JSONL 路径** — 根据源文档路径计算：去掉 `docs/` 前缀，将剩余路径的扩展名改为 `.jsonl`，前缀改为 `golden/`
- **分块列表** — 每个分块的 `id`、`index`、`heading`、`content`

将上述信息保存到上下文中供续生成使用。

### Step 2: 生成黄金数据集

调用 `rag-golden-testset` 技能，将分块内容作为源文档输入，生成一条黄金测试集数据。

具体操作：
1. 将分块内容整理为源文档格式
2. 使用 `rag-golden-testset` 技能生成 query、ground_truth_chunks、reference_answer 三元组
3. **ground_truth_chunks 必须使用上下文中记录的真实 chunk ID**（前端导入时数据库会校验）
4. 每次生成应选取不同的分块组合或角度，避免与已生成的条目重复

### Step 3: 追加写入 JSONL

将生成的黄金数据追加到 `golden/{relative_path}.jsonl`（路径与源文档 `docs/` 路径一一对应）：

```python
# 每行一条 JSON，追加模式
import json, os

# 源文档路径: docs/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.md
# JSONL 路径:  golden/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.jsonl
source_path = "docs/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.md"
relative = source_path.removeprefix("docs/")  # 去掉 docs/ 前缀
jsonl_path = os.path.join("golden", os.path.splitext(relative)[0] + ".jsonl")

entry = {
    "query": "生成的问题",
    "ground_truth_chunks": ["chunk_id_1", "chunk_id_2"],
    "reference_answer": "参考答案",
    "metadata": {}
}

os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
with open(jsonl_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

### Step 4: 输出结果

向用户展示：
- 生成的黄金数据条目（query、ground_truth_chunks、reference_answer）
- JSONL 文件路径：`golden/{relative_path}.jsonl`
- 提示用户可在前端导入该 JSONL 文件

## 注意事项

- 如果 `list-chunks` 返回"未找到文档"，提示用户检查路径是否正确
- 如果文档无分块数据，提示用户先执行文档处理流程
- `ground_truth_chunks` 中的 chunk ID 必须在项目中真实存在，否则前端导入时校验会拒绝
- 续生成时，如果上下文中没有分块信息（如新会话），要求用户重新贴出文档路径
- JSONL 文件为追加模式，多次生成会累积在同一文件中
