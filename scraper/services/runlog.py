from __future__ import annotations

import time
from typing import Any, Protocol


class _Writable(Protocol):
    def write(self, s: str, /) -> int | None: ...


def _ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def log_run_start(
    out: _Writable,
    *,
    scraper: str,
    **params: Any,
) -> None:
    bits = " ".join(f"{k}={v!r}" for k, v in sorted(params.items()))
    out.write(f"[{_ts()}] [{scraper}] RUN START {bits}\n")


def log_run_end(
    out: _Writable,
    *,
    scraper: str,
    pages_ok: int,
    pages_empty: int,
    created: int,
    updated: int,
    duration_s: float,
) -> None:
    out.write(
        f"[{_ts()}] [{scraper}] RUN END pages_ok={pages_ok} pages_empty={pages_empty} "
        f"created={created} updated={updated} duration_s={duration_s:.2f}\n"
    )


def log_page_request(
    out: _Writable,
    *,
    scraper: str,
    url: str,
    start: int,
    page_idx: int,
) -> None:
    out.write(
        f"[{_ts()}] [{scraper}] PAGE page_idx={page_idx} start={start} POST {url}\n"
    )


def log_page_rows(
    out: _Writable,
    *,
    scraper: str,
    start: int,
    row_count: int,
    created: int,
    updated: int,
) -> None:
    out.write(
        f"[{_ts()}] [{scraper}] ROWS start={start} count={row_count} "
        f"created={created} updated={updated}\n"
    )


def log_page_empty(out: _Writable, *, scraper: str, start: int) -> None:
    out.write(f"[{_ts()}] [{scraper}] EMPTY start={start} (stop pagination)\n")


def log_retry(
    out: _Writable,
    *,
    scraper: str,
    start: int,
    attempt: int,
    max_retries: int,
    err: BaseException,
) -> None:
    out.write(
        f"[{_ts()}] [{scraper}] RETRY start={start} attempt={attempt}/{max_retries} err={err!r}\n"
    )


def log_fatal(out: _Writable, *, scraper: str, err: BaseException) -> None:
    out.write(f"[{_ts()}] [{scraper}] FATAL err={err!r}\n")