"""Phiên HTTP lịch sự dùng chung cho mọi crawler.

Hai ràng buộc của runbook 01 §3.5 được cài cứng ở đây thay vì để mỗi crawler tự lo:
tối đa 1 request mỗi 1–2 giây, và lùi luỹ tiến khi máy chủ trả 429/403. Nhờ vậy chỉ
cần đọc một file là biết dự án đối xử với máy chủ bên kia ra sao.
"""

from __future__ import annotations

import random
import time
from typing import Any

import requests

from src import config


class CrawlError(RuntimeError):
    """Hết số lần thử lại mà vẫn không lấy được trang."""


# Mã lỗi đáng thử lại: quá tải, chặn tạm thời, lỗi phía máy chủ.
RETRY_STATUS = frozenset({403, 408, 429, 500, 502, 503, 504})


class PoliteSession:
    """requests.Session có nhịp và có lùi.

    Nhịp được tính theo thời điểm request TRƯỚC ĐÓ, nên thời gian xử lý phía mình
    được trừ vào khoảng chờ: crawl không chậm hơn mức cần thiết, nhưng cũng không bao
    giờ nhanh hơn ngưỡng đã khai báo.
    """

    def __init__(
        self,
        delay: float = config.REQUEST_DELAY_SECONDS,
        timeout: float = config.REQUEST_TIMEOUT_SECONDS,
        max_retries: int = config.MAX_RETRIES,
        backoff: float = config.BACKOFF_FACTOR,
        user_agent: str = config.USER_AGENT,
        logger=None,
    ) -> None:
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.logger = logger
        self._last_request = 0.0
        self.stats = {"requests": 0, "retries": 0, "errors": 0}

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Language": "vi-VN,vi;q=0.9",
            }
        )

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        # Nhiễu nhỏ để nhịp không đều tăm tắp như máy.
        target = self.delay + random.uniform(0, 0.4)
        if elapsed < target:
            time.sleep(target - elapsed)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """GET có nhịp và có lùi. Ném CrawlError khi đã thử hết lượt."""
        last_error: Exception | str = "chưa thử lần nào"

        for attempt in range(self.max_retries):
            self._wait()
            self._last_request = time.monotonic()
            self.stats["requests"] += 1

            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
            except requests.RequestException as exc:
                last_error = exc
            else:
                if response.status_code not in RETRY_STATUS:
                    # raise_for_status() nằm ngoài try thì 4xx không-retry thoát ra dưới
                    # dạng requests.HTTPError, trái contract "chỉ ném CrawlError" ở
                    # docstring, và giết cả run thay vì được nơi gọi bắt như lỗi crawl.
                    try:
                        response.raise_for_status()
                    except requests.HTTPError as exc:
                        raise CrawlError(f"{url} → HTTP {response.status_code}") from exc
                    return response
                last_error = f"HTTP {response.status_code}"

            self.stats["retries"] += 1
            sleep_for = self.delay * (self.backoff**attempt)
            if self.logger:
                self.logger.warning(
                    "%s → thử lại sau %.1fs (lần %d/%d): %s",
                    url,
                    sleep_for,
                    attempt + 1,
                    self.max_retries,
                    last_error,
                )
            time.sleep(sleep_for)

        self.stats["errors"] += 1
        raise CrawlError(f"bỏ cuộc sau {self.max_retries} lần thử: {url} ({last_error})")

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "PoliteSession":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
