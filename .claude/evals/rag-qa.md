## EVAL: rag-qa-reliability

### 目标
评估 Agent 可靠地完成 RAG 问答任务的能力

### Capability Evals

1. **上传文档并分块**
   - Task: 上传测试文档，验证分块结果
   - 验证: chunk 数量 > 0，content 非空

2. **检索相关 chunks**
   - Task: 根据问题检索相关 chunks
   - 验证: 返回结果数量 > 0，score > 0.5

3. **基于检索结果回答**
   - Task: 基于检索结果生成答案
   - 验证: 答案包含检索到的关键信息

### Regression Evals

1. **健康检查**
   - Task: 调用 /health 端点
   - 验证: 返回 200 状态码

2. **项目列表**
   - Task: 获取项目列表
   - 验证: 返回 JSON 数组

### 评估器

**Code Grader:**
```bash
# 健康检查
curl -s http://localhost:8000/health | grep -q "healthy" && echo "PASS" || echo "FAIL"

# 文档上传
curl -s -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test.txt" | grep -q "chunk_ids" && echo "PASS" || echo "FAIL"
```

### 成功标准
- pass@3 >= 90%
- pass^3 = 100% (关键路径)