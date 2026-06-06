import os


def cmd_download_embedding(args):
    """从 ModelScope 下载 embedding 模型到 models 文件夹"""
    model_name = args.model
    output_dir = args.output

    target_path = os.path.join(output_dir, model_name)

    if os.path.exists(target_path):
        print(f"模型已存在: {target_path}")
        return

    os.makedirs(target_path, exist_ok=True)

    print(f"正在下载模型 {model_name} 到 {target_path} ...")

    from modelscope import snapshot_download
    snapshot_download(model_name, local_dir=target_path)

    print(f"模型下载完成: {target_path}")
