
from rag.application.usecases.ask import AskUseCase
from rag.application.usecases.evaluate import EvaluateUseCase
from rag.shared.json_utils import json_from_jsonl, json_append


def cmd_ask(args, ask: AskUseCase, golden_file: str):
    """提问命令"""
    query = args.query or json_from_jsonl(golden_file)[args.index]["query"]

    print(f"======================= 提问 =======================")
    print(query)

    result = ask.execute(query=query, top_k=args.top_k)

    print(f"======================= 回答 =======================")
    print(result.answer)


def cmd_eval(args, evaluate: EvaluateUseCase, golden_file: str):
    """评测命令"""
    raw_records = json_from_jsonl(golden_file)
    records = [
        r for r in raw_records if r.get("ground_truth_chunks")
    ]

    k_list = args.k or [10]
    result = evaluate.execute(records, k_list=k_list)

    json_append(args.output, {
        "time": result.time,
        "embedding_file": result.embedding_file,
        "golden_file": result.golden_file,
        "embedder_model": result.embedder_model,
        "answerable_count": result.answerable_count,
        "recall": result.recall,
        "mrr": result.mrr,
        "latency_total_ms": result.latency_total_ms,
        "latency_avg_ms": result.latency_avg_ms,
        "failure": result.failure,
    })
