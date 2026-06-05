## ADDED Requirements

### Requirement: Project-level chunk search API
系统 SHALL 提供 `GET /api/projects/{pid}/chunks/search` 接口，支持按关键词搜索项目下的分块，用于前端分块选择器。

#### Scenario: 基本搜索
- **WHEN** 请求 `GET /api/projects/{pid}/chunks/search?q=RAG&limit=20`
- **THEN** 返回该项目下内容包含"RAG"的分块列表，最多 20 条，每条包含 id、content（截断）、heading、source_file

#### Scenario: 无搜索词
- **WHEN** 请求 `GET /api/projects/{pid}/chunks/search` 不带 q 参数
- **THEN** 返回该项目下最新 20 条分块

#### Scenario: 分页加载
- **WHEN** 请求 `GET /api/projects/{pid}/chunks/search?q=xxx&limit=20&offset=20`
- **THEN** 返回第 21-40 条匹配结果

#### Scenario: 项目无分块
- **WHEN** 项目下没有任何已处理的文档和分块
- **THEN** 返回空列表

### Requirement: Chunk search in golden dataset modal
黄金记录编辑弹窗中的分块选择器 SHALL 使用搜索+分页模式加载项目分块。

#### Scenario: 搜索分块
- **WHEN** 用户在分块选择器中输入搜索词
- **THEN** 调用 chunks/search API 按关键词搜索，展示匹配分块供勾选

#### Scenario: 滚动加载更多
- **WHEN** 用户滚动到分块列表底部
- **THEN** 自动加载下一页分块追加到列表

#### Scenario: 已选分块回显
- **WHEN** 编辑已有黄金记录时
- **THEN** 分块选择器中已关联的 ground_truth_chunks 显示为选中状态

#### Scenario: 选中分块展示
- **WHEN** 用户勾选了分块
- **THEN** 选择器下方显示"已选 N 个分块"
