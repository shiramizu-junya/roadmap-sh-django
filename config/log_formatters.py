"""Custom logging formatters for development."""

import logging

import sqlparse
from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.sql import SqlLexer


class SQLFormatter(logging.Formatter):
    """`django.db.backends` のログを sqlparse で整形し pygments で着色する。

    ``CursorDebugWrapper`` は ``extra={"duration", "sql", "params", "alias"}``
    を渡してくれるのでそこから直接読み出す。整形済み SQL を改行付きで出力する
    ため、複数行になる点に注意。
    """

    _lexer = SqlLexer()
    _terminal_formatter = TerminalFormatter()

    def format(self, record: logging.LogRecord) -> str:
        sql = getattr(record, "sql", None)
        if sql is None:
            return super().format(record)

        duration = getattr(record, "duration", 0.0)
        alias = getattr(record, "alias", "default")

        formatted_sql = sqlparse.format(
            sql,
            reindent=True,
            keyword_case="upper",
            strip_comments=False,
        )
        colored_sql = highlight(formatted_sql, self._lexer, self._terminal_formatter)

        timestamp = self.formatTime(record, self.datefmt)
        header = f"[{timestamp}] ({duration:.3f}s) [{alias}]"
        # 末尾に改行を 1 つ足してクエリ間に空行を作る
        # （StreamHandler の terminator='\n' と合わせて 2 連続改行になる）
        return f"{header}\n{colored_sql.rstrip()}\n"
