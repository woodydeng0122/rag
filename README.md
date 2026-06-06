## 项目启动

```
# 执行数据库迁移（部署前或开发时手动运行）
python -m rag migrate

# 启动 API 服务（不再自动迁移，仅校验）
python -m rag api

# 下载 embedding 模型
python -m rag download-embedding -m 200~BAAI/bge-small-zh-v1.5 -o ./models
```

### embedding 模型

模型	最大长度	维度	特点
bge-large-zh-v1.5	512	1024	同系列升级版，效果更好，但长度没变
stella-base-zh-v3-1792d	8192	1792	新模型，长文本，效果优异，MTEB中文榜单靠前
BAAI/bge-m3	8192	1024	多语言，支持长文本，支持稀疏+稠密混合检索
text2vec-large-chinese	512/1024	1024	老牌中文模型，有的版本支持 1024 长度

# 拆分策略

## md文档
1. 按 ## 切分（每个 section = 一个 chunk）
2. 短 chunk（< 200 字符）→ 与相邻 chunk 合并
3. 长 chunk（> 2000 字符）→ 按 ### 再切
4. 代码块保护：切分时不截断 ```...``` 块

-> multi-level heading

# DDD + CA

聚合根对应一个 Repository，聚合根内部的子对象不对外暴露，也没有自己的 Repository。

聚合根是整个聚合的唯一对外入口，普通 Entity 只在聚合内部存在，不对外暴露。

## Entity从贫血到充血
1. 判断哪些业务规则应该从 Use Case 移回 Entity。
永远成立的约束 → 放 Entity
业务场景的流程 → 放 Use Case

单个对象自己就能判断的 → Entity
需要外部信息、其他对象、或协调多方的 → Use Case

纯函数 →  放 Entity
副作用 → 放 Use Case

2. 领域事件
有多个不同的下游订阅方 → 加上事件收集
否则不用加 → 避免过度设计

3. 保护不变量
有复杂状态流转再加