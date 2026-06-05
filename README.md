## 项目启动

```
# 执行数据库迁移（部署前或开发时手动运行）
python -m rag migrate

# 启动 API 服务（不再自动迁移，仅校验）
python -m rag api
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