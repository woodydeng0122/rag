from __future__ import annotations


async def cmd_list_chunks(args, document_repo, chunk_repo):
    """根据文档路径查询所有分块"""
    storage_key = args.path

    doc = await document_repo.get_by_storage_key(storage_key)
    if doc is None:
        print(f"未找到文档: {storage_key}")
        return
    print(f"文档 ID: {doc.id}")
    print(f"文件名: {doc.filename}")
    print(f"状态: {doc.status}")
    print(f"分块数: {doc.chunk_count}")
    print("=" * 60)

    chunks = await chunk_repo.list_by_document(doc.id)
    if not chunks:
        print("无分块数据")
        return

    for c in chunks:
        print(f"\n--- 分块 [{c.index}] id={c.id} ---")
        if c.heading:
            print(f"标题: {c.heading}")
        if c.source_file:
            print(f"源文件: {c.source_file}")
        print(c.content)
