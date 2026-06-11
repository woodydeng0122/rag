-- 删除 IVFFlat 近似索引，改用精确搜索保证召回率
-- 当前数据量小（<1000条），精确搜索性能足够，IVFFlat 反而降低召回率
DROP INDEX IF EXISTS idx_embedding_vector;
