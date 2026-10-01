from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from sqlalchemy import text


@dataclass(frozen=True)
class SqlFile:
    path: Path
    checksum_sha256: str


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sql_file(path: Path) -> SqlFile:
    return SqlFile(path=path, checksum_sha256=file_checksum(path))


def _consume_statements(buffer: str) -> tuple[list[str], str]:
    statements: list[str] = []
    start = 0
    i = 0
    quote: str | None = None
    line_comment = False
    block_comment = False

    while i < len(buffer):
        ch = buffer[i]
        nxt = buffer[i + 1] if i + 1 < len(buffer) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                if nxt == quote:
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch == "-" and nxt == "-" and (i + 2 == len(buffer) or buffer[i + 2].isspace()):
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch == ";":
            statement = buffer[start:i].strip()
            if statement:
                statements.append(statement)
            i += 1
            start = i
            continue
        i += 1
    return statements, buffer[start:]


def iter_sql_statements(sql_text: str) -> Iterator[str]:
    ready, remainder = _consume_statements(sql_text)
    yield from ready
    if remainder.strip():
        yield remainder.strip()


def strip_database_switches(statements: Iterable[str]) -> Iterator[str]:
    # Kept for compatibility with older operational tooling. PostgreSQL
    # deployments do not need USE/database-switch statements.
    use_re = re.compile(r"^\s*USE\s+[^;]+$", re.IGNORECASE)
    for statement in statements:
        if use_re.match(statement):
            continue
        yield statement


def execute_sql_text(connection, sql_text: str, *, skip_use: bool = True, echo_results: bool = False) -> int:
    statements: Iterable[str] = iter_sql_statements(sql_text)
    if skip_use:
        statements = strip_database_switches(statements)

    count = 0
    for statement in statements:
        result = connection.execute(text(statement))
        count += 1
        if echo_results and getattr(result, "returns_rows", False):
            print({"columns": list(result.keys()), "rows": result.fetchall()})
    return count


def execute_sql_file(connection, path: Path, *, skip_use: bool = True, echo_results: bool = False) -> int:
    return execute_sql_text(connection, path.read_text(encoding="utf-8"), skip_use=skip_use, echo_results=echo_results)
