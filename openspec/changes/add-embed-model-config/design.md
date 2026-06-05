## Context

当前 RAG 系统的 embedding 模型在应用启动时全局固定（`SentenceTransformerEmbedder(settings.embedder_model)`），上传接口的 `embedder_model` 参数形同虚设。`embedding` 表向量维度硬编码为 `VECTOR(512)`，换模型会导致写入失败。需要引入模型注册机制，让项目创建时选定模型，保证同一项目内向量空间一致。

## Goals / Non-Goals

**Goals:**
- 项目创建时选定嵌入模型，创建后不可切换
- 模型注册表自动扫描本地 `models/` 目录，按存在性标记 online/offline
- 前端可查看模型列表、触发状态刷新
- 处理文档时从项目读取模型配置，动态加载对应 embedder 实例
- 向量维度与模型绑定，不再硬编码

**Non-Goals:**
- 不支持用户自行添加/注册模型（只能通过下载到 `models/` 目录 + 刷新状态）
- 不支持项目创建后切换模型（需删除项目重建）
- 不支持同一项目内不同文档使用不同模型
- 不做模型性能监控或 benchmark

## Decisions

### D1: 模型粒度为项目级，非文档级

**选择**: 项目级
**理由**: 同一项目内文档必须共享同一向量空间，否则检索时余弦相似度不可比。文档级选择会导致向量空间混乱。
**替代**: 文档级 — 灵活但危险，检索时需按模型分组，复杂度大幅上升。

### D2: 新增 `embed_model` 注册表，而非仅在 project 表加字段

**选择**: 独立 `embed_model` 表
**理由**: 模型元信息（名称、维度、状态）是独立实体，前端需要枚举可选模型列表，未来可能扩展模型管理功能。
**替代**: project 表直接加 `embed_model_name` + `embed_dimension` — 简单但无法集中管理模型状态和元信息。

### D3: 模型状态通过扫描本地文件系统判定

**选择**: 扫描 `models/` 目录，存在 `config.json` 则 online，否则 offline
**理由**: SentenceTransformer 模型下载后必有 `config.json`，其中 `hidden_size` 字段即为向量维度。无需加载模型即可判定。
**替代**: 尝试加载模型判定 — 启动慢，内存占用高。

### D4: Embedder 实例按模型名缓存，运行时动态加载

**选择**: 维护 `dict[str, SentenceTransformerEmbedder]` 缓存池，首次使用时加载
**理由**: 不同项目可能用不同模型，但不能每次请求都重新加载。缓存池按需加载，内存可控。
**替代**: 启动时加载所有 online 模型 — 内存浪费，模型多时启动慢。

### D5: `document.embedder_model` 字段删除

**选择**: 删除，模型信息从 `project.embed_model_id` 推导
**理由**: 消除冗余，避免 document 与 project 模型不一致。模型信息查项目即可。
**替代**: 保留冗余字段 — 方便单表查询，但增加一致性维护成本。

### D6: `embedding` 表向量维度不硬编码

**选择**: 建表时使用 `VECTOR` 不指定维度，由 pgvector 在插入时推断
**理由**: 不同项目可能使用不同维度的模型，固定维度会限制模型选择。
**注意**: pgvector 实际要求同列维度一致，因此需确保同一 embedding 列只存同维度向量。当前系统所有 embedding 在同一表中，如果未来需要混合维度，需按项目分表或增加维度列。当前阶段先保持单表，通过应用层校验保证一致性。

## Risks / Trade-offs

- **[内存风险] 多模型缓存占用内存** → 缓存池设置上限（如 3 个），LRU 淘汰。当前项目数量少，风险低。
- **[数据风险] embedding 表混合维度** → 应用层在写入前校验向量维度与项目 embed_dimension 一致，不一致则拒绝写入。
- **[兼容风险] 删除 document.embedder_model** → 需迁移脚本，前端详情页改为从项目信息展示模型名。
- **[扫描风险] models/ 目录结构不规范** → 扫描逻辑只识别包含 `config.json` 的子目录，跳过不规范的目录。
