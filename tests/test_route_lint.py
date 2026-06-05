"""Clean Architecture 路由层 lint — 检查 API 路由函数体是否为单行 return usecase.execute(...)

规则：
  - 被 @router.post / @router.get 装饰且含 usecase 参数的函数
  - 函数体只能有一行：return usecase.execute(...)
  - health 等不含 usecase 参数的路由豁免
"""

import ast
from pathlib import Path

import pytest

ROUTES_DIR = Path(__file__).resolve().parent.parent / "src" / "rag" / "api" / "routes"


# ── 纯函数：AST 检查逻辑 ──────────────────────────────────


def _is_route_handler(func: ast.FunctionDef) -> bool:
    """判断函数是否被 @router.post / @router.get 装饰"""
    for deco in func.decorator_list:
        if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
            if deco.func.attr in ("post", "get", "put", "delete", "patch"):
                return True
        if isinstance(deco, ast.Attribute) and deco.attr in ("post", "get", "put", "delete", "patch"):
            return True
    return False


def _has_usecase_param(func: ast.FunctionDef) -> bool:
    """判断函数参数中是否有 usecase 参数"""
    return any("usecase" in arg.arg.lower() for arg in func.args.args)


def _check_route_body(func: ast.FunctionDef, filepath: Path) -> str | None:
    """检查路由函数体是否符合规则，返回错误描述或 None"""
    if not _has_usecase_param(func):
        return None

    # 过滤掉 docstring
    body = func.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]

    if len(body) != 1:
        return f"{filepath.name}:{func.lineno}  {func.name}() 函数体有 {len(body)} 行，期望 1 行 (return usecase.execute(...))"

    stmt = body[0]
    if not isinstance(stmt, ast.Return):
        return f"{filepath.name}:{func.lineno}  {func.name}() 函数体不是 return 语句"

    if stmt.value is None or not isinstance(stmt.value, ast.Call):
        return f"{filepath.name}:{func.lineno}  {func.name}() return 值不是函数调用"

    if not (isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == "execute"):
        return f"{filepath.name}:{func.lineno}  {func.name}() return 值不是 usecase.execute(...)"

    return None


def _collect_route_errors(filepath: Path) -> list[str]:
    """检查单个路由文件，返回错误列表"""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))
    errors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _is_route_handler(node):
            err = _check_route_body(node, filepath)
            if err:
                errors.append(err)
    return errors


# ── pytest 参数化 ─────────────────────────────────────────


def _route_files() -> list[Path]:
    """收集路由目录下所有 .py 文件（排除 __init__.py）"""
    return sorted(p for p in ROUTES_DIR.glob("*.py") if p.name != "__init__.py")


@pytest.mark.parametrize(
    "filepath",
    _route_files(),
    ids=lambda p: p.name,
)
def test_route_is_single_return_usecase_execute(filepath):
    """路由函数体必须为单行 return usecase.execute(...)"""
    errors = _collect_route_errors(filepath)
    assert not errors, "\n".join(errors)
