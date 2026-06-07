---
name: "golden-from-doc"
description: "Generate a golden dataset entry from a local document. Invoke when user pastes a document local path (e.g. docs/xxx/file.md)."
---

# Golden From Doc

根据用户贴出的文档本地路径，自动执行两步流水线生成一条黄金数据集：

1. **获取分块** — 调用 `list-chunks` CLI 命令查询该文档的所有分块
2. **生成黄金数据** — 调用 `rag-golden-testset` 技能，基于分块内容生成一条黄金测试集

## 触发条件

用户贴出一个文档本地路径，格式类似：

- `docs/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.md`
- `docs\<uuid>\docs\some-file.md`

路径中通常包含 UUID 段和 `docs/` 前缀，这是文档的 `storage_key`。

## 执行步骤

### Step 1: 获取文档分块

运行 CLI 命令：

```bash
.venv\Scripts\python.exe -m rag list-chunks -p "<用户贴出的文档路径>"
```

从输出中提取：
- 文档 ID
- 分块列表（index、heading、content）

### Step 2: 生成黄金数据集

调用 `rag-golden-testset` 技能，将 Step 1 获取的分块作为源文档输入，生成一条黄金测试集数据。

具体操作：
1. 将分块内容整理为源文档格式
2. 使用 `rag-golden-testset` 技能生成 query、ground_truth_chunks、reference_answer 三元组
3. 将结果保存为 JSON 文件

### Step 3: 输出结果

向用户展示生成的黄金数据集条目，包含：
- query: 生成的问题
- ground_truth_chunks: 对应的分块 ID 列表
- reference_answer: 参考答案

## 注意事项

- 如果 `list-chunks` 返回"未找到文档"，提示用户检查路径是否正确
- 如果文档无分块数据，提示用户先执行文档处理流程
- 生成的黄金数据集条目需用户确认后才写入数据库
