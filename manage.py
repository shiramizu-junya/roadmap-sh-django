#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def start_debugpy_if_requested() -> None:
    """DEBUGPY=1 のときだけ、デバッガ（Zed など）の接続を 127.0.0.1:5678 で待つ。"""
    if os.environ.get("DEBUGPY") != "1":
        return
    # runserver は自動再起動のために親子2つのプロセスで動く。
    # リクエストを処理するのは子（RUN_MAIN=true）なので、そちらでだけ待つ
    if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
        return
    import debugpy

    debugpy.listen(("127.0.0.1", 5678))
    print("debugpy: 127.0.0.1:5678 で接続を待っています", file=sys.stderr)


def main():
    """Run administrative tasks."""
    start_debugpy_if_requested()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
