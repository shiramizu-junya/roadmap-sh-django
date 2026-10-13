import logging
import time

# ログの出し口。名前は "config.middleware"（このファイルの場所）になる
logger = logging.getLogger(__name__)


def timing_middleware(get_response):
    # ここはサーバ起動時に1回だけ動く。get_response は「次の層」
    def middleware(request):
        # ここから下は、リクエストのたびに動く
        start = time.perf_counter()
        response = get_response(request)  # 次の層へ渡す。戻ってくるとレスポンスがある
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    return middleware
