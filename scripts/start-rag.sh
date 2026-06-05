#!/bin/sh
# 检查 rag 包是否已安装
if ! python -c "import rag" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -e '.[dev]'
fi

# 启动应用
exec python -m rag api
