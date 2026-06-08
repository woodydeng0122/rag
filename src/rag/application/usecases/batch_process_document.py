from rag.application.results.batch_process_result import BatchProcessItem, BatchProcessResult
from rag.application.usecases.process_document import ProcessDocumentUseCase
from rag.domain.entities.document import DocumentStatus


class BatchProcessDocumentUseCase:
    """批量处理文档用例 — 对多个文档依次执行分块+嵌入"""

    def __init__(self, process_document_usecase: ProcessDocumentUseCase):
        self._process_document_usecase = process_document_usecase

    async def execute(self, document_ids: list[str]) -> BatchProcessResult:
        """批量处理文档，返回汇总结果"""
        results: list[BatchProcessItem] = []
        success_count = 0
        failed_count = 0

        for doc_id in document_ids:
            try:
                doc = await self._process_document_usecase.execute(doc_id)
                results.append(BatchProcessItem(
                    id=doc.id,
                    status=doc.status.value,
                    chunk_count=doc.chunk_count,
                ))
                success_count += 1
            except Exception as e:
                results.append(BatchProcessItem(
                    id=doc_id,
                    status=DocumentStatus.ERROR.value,
                    error_message=str(e),
                ))
                failed_count += 1

        return BatchProcessResult(
            total=len(document_ids),
            success=success_count,
            failed=failed_count,
            results=results,
        )
