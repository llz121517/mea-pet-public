"""
后台 asyncio 事件循环（单例线程）。

Qt UI 线程不跑 asyncio；网络/编排在此 loop 上执行。
同步阻塞（requests / 本地 TTS 子进程）通过 asyncio.to_thread 丢到线程池，
避免卡住 loop。
"""
from __future__ import annotations

import asyncio
import atexit
import threading
from concurrent.futures import Future
from typing import Any, Coroutine, Optional, TypeVar

T = TypeVar("T")

_lock = threading.Lock()
_loop: Optional[asyncio.AbstractEventLoop] = None
_thread: Optional[threading.Thread] = None


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _loop, _thread
    with _lock:
        if _loop is not None and _loop.is_running():
            return _loop

        loop = asyncio.new_event_loop()

        def _runner() -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        th = threading.Thread(target=_runner, name="meapet-asyncio", daemon=True)
        th.start()
        while not loop.is_running():
            pass
        _loop = loop
        _thread = th
        return _loop


def get_loop() -> asyncio.AbstractEventLoop:
    return _ensure_loop()


def submit(coro: Coroutine[Any, Any, T]) -> Future:
    """把协程投递到后台 loop，返回 concurrent.futures.Future。"""
    loop = _ensure_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop)


def run(coro: Coroutine[Any, Any, T], timeout: Optional[float] = None) -> T:
    """同步等待协程结果（供兼容调用方）。"""
    return submit(coro).result(timeout=timeout)


def shutdown() -> None:
    global _loop, _thread
    with _lock:
        loop, th = _loop, _thread
        _loop = None
        _thread = None
    if loop is None:
        return
    try:
        loop.call_soon_threadsafe(loop.stop)
    except Exception:
        pass
    if th is not None:
        th.join(timeout=2.0)
    try:
        loop.close()
    except Exception:
        pass


atexit.register(shutdown)
