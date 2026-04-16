from contextlib import contextmanager
from futu import OpenQuoteContext
from .config import OPEND_HOST, OPEND_PORT


@contextmanager
def get_quote_ctx():
    """获取 Futu 行情上下文，用 with 语句自动关闭连接。"""
    ctx = None
    try:
        ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
        yield ctx
    except Exception as e:
        print(f"[Futu] 连接失败: {e}")
        print(f"[Futu] 请确认 OpenD 已启动 ({OPEND_HOST}:{OPEND_PORT})")
        raise
    finally:
        if ctx is not None:
            ctx.close()
