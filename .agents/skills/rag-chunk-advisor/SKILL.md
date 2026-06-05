---
name: rag-chunk-advisor
description: 分析文档内容和结构，推荐最适合的 RAG 分块策略。当用户上传文档并想知道「怎么切比较好」「用什么分块策略」「chunk size 设多少合适」时触发。支持单文件（PDF/Markdown/纯文本/代码）和多文件目录（如 FastAPI 文档、项目文档站）两种输入模式。输出具体的分块策略建议，包含推荐策略、参数、理由，以及不推荐的方案和原因。不执行切分，只给建议。
---

# RAG 分块策略顾问

## 职责

**只做一件事**：读文档 → 分析特征 → 给出最佳分块策略建议。  
不执行切分，不输出 chunks.jsonl——那是 rag-chunk-splitter 的事。

支持两种输入模式：
- **单文件模式**：一个 PDF / Markdown / 纯文本文件
- **目录模式**：一个包含多个文档文件的文件夹（如文档站、开源项目 docs/）

---

## 分析流程

### Step 0（目录模式专属）：目录探索与分组

当输入是文件夹路径时，先执行此步骤，再进入 Step 1。

**0.1 扫描目录结构**

```python
import os
from pathlib import Path

def scan_docs_dir(root: str):
    stats = []
    for path in Path(root).rglob("*"):
        if path.is_file() and path.suffix in {".md", ".rst", ".txt", ".html", ".pdf"}:
            size = path.stat().st_size
            stats.append({
                "path": str(path.relative_to(root)),
                "suffix": path.suffix,
                "size_bytes": size,
                "subdir": str(path.parent.relative_to(root))
            })
    return stats
```

输出一份文件清单，统计：
- 文件总数、总大小
- 按子目录分组的文件数量和平均大小
- 文件大小分布（最小 / 中位 / 最大 / P90）
- 主要文件类型比例

**0.2 目录语义分组**

根据子目录名称推断内容类型，典型映射如下：

| 目录名模式 | 推断内容类型 | 典型特征 |
|-----------|-------------|---------|
| `tutorial/`, `guide/`, `walkthrough/` | 教程型 | 长文、叙述型、步骤多 |
| `reference/`, `api/`, `endpoints/` | API 参考型 | 短文、结构化、参数列表密集 |
| `how-to/`, `cookbook/`, `examples/` | 操作指南型 | 中等长度、代码多 |
| `concepts/`, `explanation/`, `about/` | 概念解释型 | 中长文、叙述型 |
| `changelog/`, `release-notes/` | 变更记录型 | 列表密集、时间序列 |
| `faq/` | FAQ 型 | 短问答密集 |

> 若目录名无法推断，则抽样 2-3 个文件后判断。

**0.3 抽样策略**

不逐一读取所有文件，按分组抽样：
- 每个语义分组抽 **2-3 个文件**（选最小、中位、最大各一个）
- 总抽样文件数上限：**10 个**
- 抽样后走 Step 1-2 的单文件分析流程

**0.4 判断是否需要差异化策略**

| 判断条件 | 结论 |
|---------|------|
| 所有子目录内容类型相同、文件大小 P90/P10 比值 < 5 | **统一策略**：一套参数覆盖全部文件 |
| 存在 2 种以上明显不同的内容类型（如 tutorial + reference） | **分组策略**：每组独立配置 |
| 存在超大文件（> 50k 字符）混在普通文件中 | **混合策略**：大文件单独处理 |

---

### Step 1：读取文档（单文件 / 抽样文件）

先用合适的方式读取文档内容：
- PDF → 用 `pdfplumber` 或 `pymupdf` 提取文本；**同时**用 `pymupdf`（`page.get_images()`）检测是否含有嵌入图片
- Markdown / 纯文本 / 代码 → 直接读取
- 读取前 3000 字符做快速预览，再抽样中间和末尾各 1000 字符

**PDF 图片/图表检测**（仅 PDF 需要）：

```python
import fitz  # pymupdf

doc = fitz.open("file.pdf")
image_pages = []
for i, page in enumerate(doc):
    if page.get_images():
        image_pages.append(i + 1)

has_images = len(image_pages) > 0
image_ratio = len(image_pages) / len(doc)  # 含图页面占比
```

根据结果判断图片类型：
- `image_ratio > 0.8` → 很可能是扫描件或幻灯片导出
- `image_ratio < 0.3` → 少量插图，主要是文字文档
- 文字提取后字符数极少（< 100字/页均值）→ 扫描件，文字提取无效

---

### Step 2：提取文档特征

分析以下维度，为每项打标：

| 维度 | 观察点 |
|------|--------|
| **结构化程度** | 有无标题层级（#/##/###）、列表、分节 |
| **段落长度** | 平均段落字数，是否均匀 |
| **内容类型** | 叙述型 / FAQ / 技术文档 / 代码 / 表格密集 / 对话记录 |
| **语言** | 中文 / 英文 / 混合（影响分隔符选择） |
| **文档总长** | 短文（<5k字） / 中等（5k–50k） / 长文（>50k） |
| **答案分布** | 答案是否可能跨段落（叙述型风险高，FAQ 风险低） |
| **特殊元素** | 表格、代码块、公式、图片说明（这些不能被截断） |
| **图片/图表** | 见下方专项分析 |

**目录模式补充**：对每个抽样文件单独打标，然后在 Step 0.4 的分组基础上汇总每组的共同特征。

---

### Step 2.1：Section 大小分布分析（关键决策依据）

在 Step 2 特征提取后，**必须**执行此分析——它决定最终用「统一策略」还是「分组策略」。

**方法**：按 `##` 标题将文档切为 section，统计每个 section 的字符数。

```python
import re
from pathlib import Path

def analyze_sections(root: str):
    all_sections = []
    for p in Path(root).rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        parts = re.split(r"^(## )", text, flags=re.M)
        sections = []
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                sec = parts[i] + (parts[i+1] if i+1 < len(parts) else "")
                sections.append(sec.strip())
            if parts[0].strip():
                sections.insert(0, parts[0].strip())
        else:
            sections = [text.strip()] if text.strip() else []
        for s in sections:
            all_sections.append(len(s))
    return sorted(all_sections)
```

**输出统计**：

| 指标 | 含义 |
|------|------|
| section 总数 | 文档按 `##` 切后有多少个 section |
| 理想区间占比 | 200–1200 字符的 section 占比 |
| 太短占比 | < 200 字符的 section 占比（需合并） |
| 太长占比 | > 2000 字符的 section 占比（需再切） |
| P90/P10 比值 | section 大小差异程度 |

**决策规则**：

| 条件 | 结论 |
|------|------|
| 理想区间占比 ≥ 80%，太短+太长合计 < 20% | **优先用 section-heading 统一策略**（见 Step 3） |
| 理想区间占比 60%–80%，但不同目录 section 大小分布差异大 | **分组策略**：每组独立配置 |
| 理想区间占比 < 60% | **回退到 separator 策略**：用 `["\n## ", "\n### ", "\n\n"]` + chunk_size 控制 |

> **核心洞察**：很多技术文档按 `##` 切后，section 天然就是好 chunk（200–1200 字符）。
> 此时不需要分组差异化配置，一套 section-heading 规则即可覆盖 80%+ 场景。

---

### Step 2.5：PDF 图片/图表专项分析

检测到 PDF 含图片时，进一步判断图表类型并给出对应处理建议：

| 情况 | 判断方式 | 推荐处理方向 |
|------|----------|--------------|
| **图表有 caption / 说明文字** | 图片附近（前后2行）能提取到"图X"、"Figure"、"如图所示"等文字 | caption 随正文切分；提示用户图片视觉内容丢失，可接受 |
| **图表无说明文字** | 图片附近无任何描述文字 | ⚠️ 高风险：检索时视觉内容完全不可见，需额外处理 |
| **表格是真实文本**（非图片） | pdfplumber 能提取到结构化行列 | 整体保留为单个 chunk，不在表格内部截断 |
| **表格是图片**（截图/扫描） | 提取结果为空或乱码 | 同"图表无说明"，需额外处理 |
| **扫描件 / 全图 PDF** | 每页字符数 < 100，image_ratio > 0.8 | 文本切分完全无效，必须先 OCR |

**针对含图/图表的 PDF，给出分级建议**：

```
🖼️  图片/图表处理建议

情况：检测到 N 张嵌入图片，分布在第 X、Y、Z 页

方案 A（轻量，适合图表信息非核心）
  → 提取文字部分正常切分
  → caption 跟随相邻段落一起进入 chunk
  → 接受图表视觉内容的信息损失
  → 适用：图表只是辅助说明，用户不会针对图表内容提问

方案 B（推荐，适合图表信息重要）
  → 用 Vision LLM 对每页含图页面生成图片描述
  → 描述文本作为独立 chunk 插入，metadata 标注 type: "image_description"
  → chunk 示例：
     {"id": "report_img_p12", "text": "第12页图表：2023年Q1-Q4销售额分别为
      120万、145万、132万、178万，Q4环比增长34.8%",
      "type": "image_description", "source_page": 12}
  → 适用：图表含关键数据，用户会针对图表内容提问

方案 C（完整，适合扫描件 / 高图片比例 PDF）
  → 先用 OCR（tesseract / Azure Form Recognizer / AWS Textract）全文识别
  → OCR 结果再走正常文本分块流程
  → 图表另用 Vision LLM 生成描述，插入对应位置
  → 成本最高，但信息损失最少
  → 适用：合同、报告、学术论文扫描件
```

---

### Step 3：匹配策略

根据特征组合，从下表选出最佳策略（可以是组合）：

| 策略 | 适用特征 | 推荐参数 |
|------|----------|----------|
| **section-heading**（按标题切 + 边界修正） | 有清晰 `##` 标题层级，section 大小分布理想（≥80% 在 200–1200 字符） | 见下方 4 条规则 |
| **semantic**（语义/结构边界切） | 有标题层级但 section 大小不理想，需 chunk_size 控制 | 按 `\n\n` + 标题边界，chunk_size=600–1000 字符，overlap=0 |
| **fixed**（固定大小） | 结构平坦、段落均匀、通用叙述型 | chunk_size=400–600 字符，overlap=50–80 字符 |
| **large-overlap**（大重叠） | 长叙述型、答案易跨段、故事/报告 | chunk_size=512 字符，overlap=128–200 字符 |
| **sentence**（句子级） | FAQ、对话记录、短问答密集型 | 按句子切，每 chunk 3–5 句，overlap=1 句 |
| **no-split**（不切） | 极短文档（<1k字符），直接全文入 context | 无需分块 |

**section-heading 策略详解**（优先推荐，实现最简）：

当 Step 2.1 的分析显示 section 大小分布理想时，只需 4 条规则：

```
1. 按 ## 切分（每个 section = 一个 chunk）
2. 短 chunk（< 200 字符）→ 与相邻 chunk 合并，直到 ≥ 200 字符
3. 长 chunk（> 2000 字符）→ 按 ### 子标题进一步切分
4. 代码块保护：切分时不截断 ```...``` 块
```

**section-heading vs semantic 的区别**：

| 维度 | section-heading | semantic |
|------|----------------|----------|
| 切分依据 | 先按 `##` 切，再修正边界 | 按 separator + chunk_size 切 |
| chunk_size | 不需要（section 天然就是好大小） | 必须指定 |
| overlap | 不需要（section 边界即语义边界） | 通常需要 |
| 实现复杂度 | 低（4 条规则） | 中（需调 separator + size + overlap） |
| 适用前提 | ≥80% section 在 200–1200 字符 | 无特殊前提 |

**混合策略**：正文用 semantic/section-heading，代码块和表格整体保留为单个 chunk（不截断）。

**目录模式的分组策略示例**（以 FastAPI 文档为例）：

| 分组 | 目录 | 内容特征 | 推荐策略 |
|------|------|---------|---------|
| 教程组 | `tutorial/` | 长文、叙述型、步骤多 | semantic，chunk_size=800，overlap=80 |
| API参考组 | `reference/` | 短文、参数列表密集 | semantic，chunk_size=400，overlap=0 |
| 操作指南组 | `how-to/` | 中等长度、代码多 | semantic + 代码块保护，chunk_size=600 |
| 概念组 | `concepts/` | 中长叙述型 | large-overlap，chunk_size=512，overlap=128 |

---

### Step 4：Metadata 策略（目录模式必须输出）

多文件场景下，每个 chunk 必须携带足够的 metadata 才能支持过滤和溯源。

**必须字段**：

```json
{
  "id": "fastapi_tutorial_first-steps_chunk_3",
  "text": "...",
  "source_file": "docs/tutorial/first-steps.md",
  "source_dir": "tutorial",
  "doc_type": "tutorial",
  "chunk_index": 3,
  "total_chunks_in_file": 8
}
```

**推荐附加字段**（视情况）：

```json
{
  "heading": "Path Parameters",
  "file_size_bucket": "medium",
  "language": "en",
  "has_code": true
}
```

**metadata 的用途**：
- `source_dir` / `doc_type` → 支持按栏目过滤检索（如只搜 API reference）
- `heading` → 提升召回的可解释性
- `chunk_index` + `total_chunks_in_file` → 支持上下文扩展（检索到第 3 块时顺带取第 2、4 块）

---

### Step 5：输出建议报告

---

## 输出格式

### 单文件模式

```
📄 文档分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
文件名：xxx.md
总字数：约 12,400 字
语言：中文（含少量英文术语）
内容类型：技术文档，有清晰章节结构
特殊元素：代码块 ×8，表格 ×3，嵌入图片 ×5（分布在第 4、7、12、15、20 页）

🔍 关键特征
  ✅ 有三级标题层级（#/##/###）
  ✅ 段落长度均匀（平均 180 字/段）
  ⚠️  代码块最长 420 字，截断会破坏语义
  ✅ FAQ 式内容较少，答案不跨段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 推荐策略：semantic + 代码块保护

  主策略：semantic
    separators: ["\n## ", "\n### ", "\n\n"]
    chunk_size: 800 字符
    overlap: 0

  补充规则：
    - 检测到代码块（```...```）时整体保留，不在内部截断
    - 表格同理，整体作为一个 chunk

  理由：
    文档有清晰章节边界，每节内容独立，按标题切可以保证
    语义完整；代码块和表格若被截断会导致检索结果残缺。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 不推荐

  fixed（固定大小）
    原因：会在代码块中间切断，破坏代码完整性

  large-overlap（大重叠）
    原因：文档结构清晰，答案不跨段，大重叠只增加冗余 token

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 后续建议
  用 rag-chunk-splitter 执行切分时，传入以上参数
  切完后建议用 rag-chunk-quality-check 抽样检查代码块是否完整
```

### 目录模式

**情况 A：section 大小分布理想 → section-heading 统一策略**

```
📁 目录分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
根目录：fastapi/docs/
文件总数：123 个
总大小：704.7 KB
主要类型：.md（100%）
语言：中文（含英文代码/术语）

📊 Section 大小分布（按 ## 切）
  section 总数：711
  理想区间（200–1200）：82.6%  ✅
  太短（< 200）：25.5%  → 需合并
  太长（> 2000）：5.9%   → 需再切
  P90/P10 比值：11.8

🔍 跨文件共同特征
  ✅ 全部文件有 ## 标题层级
  ✅ 代码块普遍存在（平均每文件 3–4 个）
  ✅ 无 PDF，无扫描件，纯 Markdown

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 推荐策略：section-heading（统一，4 条规则）

  1. 按 ## 切分（每个 section = 一个 chunk）
  2. 短 chunk（< 200 字符）→ 与相邻 chunk 合并
  3. 长 chunk（> 2000 字符）→ 按 ### 再切
  4. 代码块保护：不截断 ```...``` 块

  理由：
    82.6% 的 section 天然落在 200–1200 字符的理想区间，
    按标题切即可保证语义完整，无需分组差异化配置。
    短 section 多为 index/过渡段落，合并即可；
    长 section 仅 5.9%，按 ### 再切即可。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 不推荐

  分组差异化配置
    原因：section 大小分布理想时，分组策略增加实现复杂度
    但不提升召回质量——按 ## 切已经是语义最优边界

  全目录统一 fixed（固定大小）
    原因：会在代码块中间切断，破坏代码完整性

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 后续建议
  1. 用 rag-chunk-splitter 传入以上 4 条规则执行切分
  2. 切完后用 rag-chunk-quality-check 抽样检查
  3. 重点检查：代码块是否被截断、短 chunk 合并后是否语义连贯
```

**情况 B：section 大小分布不理想 → 分组差异化配置**

```
📁 目录分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
根目录：fastapi/docs/
文件总数：147 个
总大小：约 2.3 MB
主要类型：.md（92%）、.rst（8%）
语言：英文

📊 文件大小分布
  最小：0.4 KB（changelog 条目）
  中位：8.2 KB
  P90：34 KB
  最大：89 KB（tutorial/bigger-applications.md）

📂 子目录分组（基于抽样分析）
  tutorial/      42 个文件，均值 18 KB → 教程型，叙述+代码混合
  reference/     38 个文件，均值  4 KB → API 参考型，参数列表密集
  how-to/        21 个文件，均值 10 KB → 操作指南型，代码为主
  concepts/      12 个文件，均值 14 KB → 概念解释型，叙述为主
  changelog/     34 个文件，均值  1 KB → 变更记录型，列表密集

🔍 跨文件共同特征
  ✅ 全部文件有标题层级（## / ###）
  ✅ 代码块普遍存在，平均每文件 6 个
  ⚠️  tutorial/ 中部分文件超过 50k 字符，需特殊处理
  ✅ 无 PDF，无扫描件，纯文本处理

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 推荐策略：分组差异化配置

  【tutorial/ + concepts/】叙述型长文组
    策略：semantic + large-overlap
    separators: ["\n## ", "\n### ", "\n\n"]
    chunk_size: 800 字符
    overlap: 100 字符
    超大文件（>50k）：先按顶级 ## 标题拆分为子文件，再切块

  【reference/】API 参考型短文组
    策略：semantic（无 overlap）
    separators: ["\n## ", "\n### ", "\n\n"]
    chunk_size: 400 字符
    overlap: 0
    理由：每个参数条目独立，overlap 只增加噪声

  【how-to/】操作指南型
    策略：semantic + 代码块保护
    separators: ["\n## ", "\n### ", "\n\n"]
    chunk_size: 600 字符
    overlap: 60 字符

  【changelog/】变更记录型
    策略：sentence（按版本号条目切）
    每 chunk 合并 1 个版本条目，不跨版本
    chunk_size: 300 字符上限

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️  Metadata 方案

  必须字段：
    source_file, source_dir, doc_type, chunk_index, total_chunks_in_file

  推荐字段：
    heading（所属标题）, has_code（是否含代码块）

  过滤建议：
    建立 doc_type 过滤索引，支持「只搜 API 参考」或「只搜教程」

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 不推荐

  全目录统一 fixed（固定大小）
    原因：reference/ 文件很短，fixed 会把多个 API 条目混在一个 chunk，
          检索时引入无关内容；tutorial/ 文件又很长，overlap 不够会丢上下文

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 后续建议
  1. 按分组分别调用 rag-chunk-splitter，传入对应参数
  2. tutorial/ 超大文件建议先用脚本按 ## 切成子文件
  3. 切完后用 rag-chunk-quality-check 对每组各抽 20 个 chunk 检查
  4. 特别检查代码块是否被截断（how-to/ 组风险最高）
```

---

## 边界情况处理

- **无法读取文档**（加密 PDF、损坏文件）→ 告知原因，请用户提供可读版本
- **混合语言文档** → 分隔符同时包含中英文标点（`。`, `.`, `\n`）
- **纯表格/数据文件**（CSV、Excel）→ 建议按行或按逻辑分组切，不适用本技能，转告用户
- **超大文档（>200k字）** → 建议先按顶级章节拆分文件，再分别切块
- **扫描件 PDF**（每页字符 < 100）→ 直接告知文本切分无效，必须先走 OCR 流程，推荐方案 C
- **图表信息是否重要不确定** → 默认推荐方案 B，并告知用户三种方案的成本与信息损失权衡
- **目录文件数 > 500** → 不逐一读取；按子目录各抽 1-2 个文件，并告知用户分析基于抽样
- **目录结构扁平（无子目录）** → 按文件大小分桶（small/medium/large）代替目录分组，各桶抽样分析
- **文件命名无语义（如 doc1.md, doc2.md）** → 无法通过目录名推断类型，改为纯内容抽样判断
- **目录中存在非文档文件**（图片、视频、压缩包等）→ 跳过并在报告中注明忽略文件列表
- **section-heading 策略下短 chunk 合并方向不确定** → 优先向后合并（与下一个 section 合并），除非下一个 section 属于不同 `#` 顶级标题
- **section-heading 策略下长 chunk 按 ### 切后仍超 2000 字符** → 再按 `\n\n` 段落边界切，但代码块/表格仍不可截断；若单个代码块就超 2000 字符，则整个代码块作为独立 chunk