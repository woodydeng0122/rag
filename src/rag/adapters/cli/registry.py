"""CLI 命令注册表 — 命令自描述，按需加载依赖"""
from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Any, Callable, Literal


@dataclass
class CliCommand:
    """命令描述"""

    name: str
    help: str
    dependency: Literal["none", "db", "full_container"]
    register_args: Callable[[ArgumentParser], None]
    handler: Callable[..., Any]


# 全局命令注册表
COMMANDS: list[CliCommand] = []


def register_command(
    name: str,
    help: str,
    dependency: Literal["none", "db", "full_container"],
    register_args: Callable[[ArgumentParser], None],
    handler: Callable[..., Any],
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
    """
    COMMANDS.append(
        CliCommand(
            name=name,
            help=help,
            dependency=dependency,
            register_args=register_args,
            handler=handler,
        )
    )
