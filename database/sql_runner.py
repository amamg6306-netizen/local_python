from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


_DELIMITER_RE = re.compile(r"^\s*DELIMITER\s+(\S+)\s*$", re.IGNORECASE)
_USE_RE = re.compile(r"^\s*USE\s+`?([A-Za-z0-9_$-]+)`?\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class SqlFile:
    path: Path
    checksum_sha256: str


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sql_file(path: Path) -> SqlFile:
    return SqlFile(path=path, checksum_sha256=file_checksum(path))


def _consume_statements(buffer: str, delimiter: str) -> tuple[list[str], str]:
    statements: list[str] = []
    start = 0
    i = 0
    quote: str | None = None
    backtick = False
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
        if backtick:
            if ch == "`":
                backtick = False
            i += 1
            continue

        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch == "`":
            backtick = True
            i += 1
            continue
        if ch == "#":
            line_comment = True
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

        if buffer.startswith(delimiter, i):
            statement = buffer[start:i].strip()
            if statement:
                statements.append(statement)
            i += len(delimiter)
            start = i
            continue
        i += 1

    return statements, buffer[start:]


def _comment_only(value: str) -> bool:
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
    value = re.sub(r"(?m)^\s*(?:--(?:\s|$)|#).*?$", "", value)
    return not value.strip()


def iter_mysql_statements(sql_text: str) -> Iterator[str]:
    delimiter = ";"
    buffer = ""

    for raw_line in sql_text.splitlines(keepends=True):
        match = _DELIMITER_RE.match(raw_line.rstrip("\r\n"))
        if match:
            ready, remainder = _consume_statements(buffer, delimiter)
            for statement in ready:
                yield statement
            if remainder.strip() and not _comment_only(remainder):
                raise ValueError("DELIMITER changed while an SQL statement was incomplete.")
            buffer = ""
            delimiter = match.group(1)
            continue

        buffer += raw_line
        ready, buffer = _consume_statements(buffer, delimiter)
        for statement in ready:
            yield statement

    if buffer.strip():
        yield buffer.strip()


def _sql_without_leading_comments(statement: str) -> str:
    value = statement.lstrip()
    while True:
        previous = value
        value = re.sub(r"^/\*.*?\*/\s*", "", value, count=1, flags=re.S)
        value = re.sub(r"^(?:--(?:\s|$)|#).*?(?:\n|$)\s*", "", value, count=1)
        if value == previous:
            return value


def strip_database_switches(statements: Iterable[str]) -> Iterator[str]:
    for statement in statements:
        if _USE_RE.match(_sql_without_leading_comments(statement)):
            continue
        yield statement


def execute_sql_text(connection, sql_text: str, *, skip_use: bool = True, echo_results: bool = False) -> int:
    statements: Iterable[str] = iter_mysql_statements(sql_text)
    if skip_use:
        statements = strip_database_switches(statements)

    count = 0
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
            count += 1
            if echo_results and cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                print({"columns": columns, "rows": rows})
    return count


def execute_sql_file(connection, path: Path, *, skip_use: bool = True, echo_results: bool = False) -> int:
    return execute_sql_text(
        connection,
        path.read_text(encoding="utf-8"),
        skip_use=skip_use,
        echo_results=echo_results,
    )
