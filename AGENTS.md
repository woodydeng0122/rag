# 前端项目为独立仓库
- `./rag-web`

# 代码规范
1. 加载 `clean-architecture` 技能
2. 夹杂 `design-principles` 技能
2. 优先使用绝对路径

# 执行脚本时
- 禁止执行项目开发启动脚本(pnpm dev|python -m rag api)，如有需求告知用户
- 执行其他Python脚本前, 先运行: source .venv/bin/activate

# 有代码改动时自检
1. 是否符合: clean-architecture
2. design-principles 逐一检查
3. 下一步建议
