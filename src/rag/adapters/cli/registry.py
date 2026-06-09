"""CLI 命令注册表 — 命令自描述，按需加载依赖"""
from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, field
from typing import Any, Callable, Literal


@dataclass
class CliCommand:
    """命令描述"""

    name: str
    help: str
    dependency: Literal["none", "db", "full_container"]
    _register_args: Callable[[ArgumentParser], None] | None = field(default=None, repr=False)
    _handler: Callable[..., Any] | None = field(default=None, repr=False)
    _lazy_import: str | None = field(default=None, repr=False)

    @property
    def register_args(self) -> Callable[[ArgumentParser], None]:
        if self._register_args is not None:
            return self._register_args
        if self._lazy_import:
            self._load()
            return self._register_args
        raise RuntimeError(f"命令 {self.name} 未注册 register_args")

    @property
    def handler(self) -> Callable[..., Any]:
        if self._handler is not None:
            return self._handler
        if self._lazy_import:
            self._load()
            return self._handler
        raise RuntimeError(f"命令 {self.name} 未注册 handler")

    def _load(self):
        """延迟导入模块并填充 register_args 和 handler"""
        module_path = self._lazy_import
        import importlib
        mod = importlib.import_module(module_path)
        self._register_args = mod.register_args
        self._handler = mod.handle


# 全局命令注册表
COMMANDS: list[CliCommand] = []


def register_command(
    name: str,
    help: str,
    dependency: Literal["none", "db", "full_container"],
    register_args: Callable[[ArgumentParser], None] | None = None,
    handler: Callable[..., Any] | None = None,
    lazy_import: str | None = None,
):
    """注册 CLI 命令

    dependency:
      - "none": 无外部依赖
      - "db": 仅需数据库连接池
      - "full_container": 需完整容器（embedder、LLM 等）

    handler 签名:
      - dependency="none":  handler(args)
      - dependency="db":    handler(args, settings)
      - dependency="full_container": handler(args, container)

    lazy_import:
      - 模块路径，如 "rag.adapters.cli.migrate"
      - 模块需暴露 register_args 和 handle 函数
      - 设置后 register_args 和 handler 可省略，首次访问时延迟加载
    """
    COMMANDS.append(
        CliCommand(
            name=name,
            help=help,
            dependency=dependency,
            _register_args=register_args,
            _handler=handler,
            _lazy_import=lazy_import,
        )
    )
