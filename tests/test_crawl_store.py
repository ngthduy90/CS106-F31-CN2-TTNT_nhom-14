"""Kiểm tra kho thô, checkpoint và tầng HTTP.

Ba module này chưa từng có test, mà đúng là chỗ có failure mode "âm thầm mất dữ
liệu": checkpoint hỏng làm lần chạy sau chết trước khi crawl, dedup hỏng làm kho
phình, và một lỗi 4xx thoát ra sai kiểu thì giết cả phiên thay vì được xử lý.
"""

import json

import pytest
import requests

from src.crawl.http import CrawlError, PoliteSession
from src.crawl.store import Checkpoint, RawStore


def test_checkpoint_ghi_atomic_va_khong_de_lai_rac(tmp_path):
    checkpoint = Checkpoint("chotot", "Tân Bình", root=tmp_path)
    checkpoint.save(written_total=12)
    assert json.loads(checkpoint.path.read_text(encoding="utf-8"))["written_total"] == 12
    assert list(checkpoint.path.parent.glob("*.tmp")) == []


def test_checkpoint_hong_khong_giet_lan_chay_sau(tmp_path):
    """JSON cụt (bị giết giữa lúc ghi) phải đọc thành trạng thái rỗng, không ném."""
    first = Checkpoint("chotot", "Tân Bình", root=tmp_path)
    first.save(written_total=5)
    first.path.write_text('{"written_total": 5', encoding="utf-8")  # cụt

    second = Checkpoint("chotot", "Tân Bình", root=tmp_path)
    assert second.get("written_total") is None
    second.save(written_total=7)
    assert second.get("written_total") == 7


def test_checkpoint_reset_xoa_file(tmp_path):
    checkpoint = Checkpoint("chotot", "Quận 12", root=tmp_path)
    checkpoint.save(written_total=3)
    checkpoint.reset()
    assert not checkpoint.path.exists()
    assert checkpoint.get("written_total") is None


def test_raw_store_bo_qua_tin_trung_va_cap_nhat_seen_ids_ngay(tmp_path):
    store = RawStore("chotot", "Tân Bình", "list_id", root=tmp_path)
    assert store.append({"list_id": 1, "body": "tin A"}) is True
    # seen_ids là tập SỐNG: tin vừa ghi phải thấy ngay trong cùng lần chạy.
    assert "1" in store.seen_ids
    assert store.append({"list_id": 1, "body": "tin A"}) is False
    assert store.written == 1 and store.skipped_duplicate == 1


def test_raw_store_xoa_so_dien_thoai_truoc_khi_ghi(tmp_path):
    store = RawStore("chotot", "Tân Bình", "list_id", root=tmp_path)
    store.append({"list_id": 9, "body": "Bán nhà, LH 0901234567"})
    written = json.loads(store.path.read_text(encoding="utf-8").strip())
    assert "0901234567" not in written["body"]
    assert store.pii_redactions == 1


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = ""

    def raise_for_status(self):
        raise requests.HTTPError(f"{self.status_code}", response=self)


def test_4xx_khong_retry_ra_crawl_error(monkeypatch):
    """Contract của get() là "chỉ ném CrawlError"; HTTPError lọt ra giết cả run."""
    session = PoliteSession(delay=0, max_retries=2)
    monkeypatch.setattr(session.session, "get", lambda *a, **k: _FakeResponse(404))

    with pytest.raises(CrawlError):
        session.get("https://example.test/tin/1")
