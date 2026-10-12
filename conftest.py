import os
import sys


def pytest_configure() -> None:
    """DEBUGPY=1 のときだけ、デバッガ（Zed など）の接続を待ってからテストを始める。"""
    if os.environ.get("DEBUGPY") != "1":
        return
    # Python 本体の一部（frozen modules）について出る警告を止める。自分のコードの停止には影響しない
    os.environ.setdefault("PYDEVD_DISABLE_FILE_VALIDATION", "1")
    import debugpy

    # サーバ（runserver）は 5678。テストは 5679 にして、同時に動かしてもぶつからないようにする
    port = int(os.environ.get("DEBUGPY_PORT", "5679"))
    debugpy.listen(("127.0.0.1", port), in_process_debug_adapter=True)
    print(f"debugpy: 127.0.0.1:{port} で接続を待っています", file=sys.stderr)
    debugpy.wait_for_client()  # テストはすぐ終わるので、つながるまで待つ
