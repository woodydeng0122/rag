import json


def json_from_jsonl(file_path: str, encoding: str = 'utf-8') -> list:
    with open(file_path, 'r', encoding=encoding) as f:
        return [json.loads(line) for line in f if line.strip()]


def json_append(file_path: str, data) -> None:
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([data], f, ensure_ascii=False, indent=4)
    else:
        with open(file_path, 'r+', encoding='utf-8') as f:
            data_list = json.load(f)
            data_list.append(data)
            f.seek(0)
            json.dump(data_list, f, ensure_ascii=False, indent=4)
            f.truncate()
