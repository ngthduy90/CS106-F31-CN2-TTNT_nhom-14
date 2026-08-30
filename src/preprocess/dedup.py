"""T2.9 — khử trùng lặp, điều kiện tiên quyết của mọi thí nghiệm.

Môi giới đăng lại cùng một căn nhiều lần, và cùng một căn thường có mặt trên cả hai
sàn. Nếu hai bản của một căn rơi vào cả tập train lẫn tập test thì mô hình được xem
trước đáp án: chỉ số đẹp lên mà không có nghĩa gì. Vì vậy bước này chạy TRƯỚC khi chia
tập, không phải sau.

So từng cặp trong 100.000 dòng là 5 tỷ phép so — không khả thi. Cách làm theo runbook
02 §3.1 gồm ba tầng lọc dần:

1. **Chặn (blocking)**: chỉ so các tin cùng (phường, diện tích làm tròn 5 m²). Hai tin
   khác phường hoặc lệch diện tích quá 5 m² thì không thể là cùng một căn.
2. **Tương đồng văn bản**: TF-IDF trên n-gram KÝ TỰ (3–5) rồi cosine ≥ 0,85. Dùng
   n-gram ký tự chứ không phải từ vì bản đăng lại hay đổi vài từ, thêm emoji, viết
   hoa khác đi — mức ký tự chịu được các thay đổi đó.
3. **Giá gần nhau**: chênh không quá 3%. Hai căn chung cư cùng toà có thể có mô tả
   giống hệt nhau; giá là thứ tách chúng ra.

Bản được giữ lại là bản MỚI NHẤT, hoà thì lấy bản có mô tả DÀI NHẤT (nhiều thông tin
hơn cho bước trích đặc trưng).
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src import config

AREA_BLOCK_M2 = 5  # bề rộng ô chặn theo diện tích


def _block_key(row) -> tuple:
    area = row["area_m2"]
    bucket = int(area // AREA_BLOCK_M2) if pd.notna(area) else -1
    return (row["district"], row["ward"], bucket)


def find_duplicate_groups(
    frame: pd.DataFrame,
    text_threshold: float = config.DUPLICATE_TEXT_COSINE,
    price_tolerance: float = config.DUPLICATE_PRICE_TOLERANCE,
    max_block_size: int = config.DUPLICATE_MAX_BLOCK_SIZE,
) -> tuple[list[list[int]], list[dict], dict]:
    """Các nhóm dòng được coi là cùng một bất động sản, kèm mẫu cặp và thống kê ô."""
    blocks: dict[tuple, list[int]] = defaultdict(list)
    for position, (_, row) in enumerate(frame.iterrows()):
        blocks[_block_key(row)].append(position)

    parent = list(range(len(frame)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    texts = (frame["title"].fillna("") + " " + frame["description"].fillna("")).to_numpy()
    prices = frame["total_price_vnd"].to_numpy(dtype="float64")
    samples: list[dict] = []

    block_stats = {"ô đã chia nhỏ": 0, "dòng trong ô đã chia nhỏ": 0}

    # Ô quá lớn (phường đông tin, diện tích phổ biến) trước đây bị BỎ QUA nguyên khối,
    # không đếm, không log — mà đó lại đúng là nơi trùng lặp tập trung, nên mọi cặp bên
    # trong sống sót vào bảng rồi bị splits chia hai phía. Giờ chia nhỏ theo thập phân
    # vị giá (khoá phụ rẻ, cặp trùng gần như luôn cùng bậc giá) thay vì bỏ.
    work: list[list[int]] = []
    for members in blocks.values():
        if len(members) < 2:
            continue
        if len(members) <= max_block_size:
            work.append(members)
            continue
        block_stats["ô đã chia nhỏ"] += 1
        block_stats["dòng trong ô đã chia nhỏ"] += len(members)
        ranked = sorted(members, key=lambda i: (prices[i] if np.isfinite(prices[i]) else -1.0))
        chunks = max(2, -(-len(ranked) // max_block_size))
        size = -(-len(ranked) // chunks)
        for start in range(0, len(ranked), size):
            piece = ranked[start : start + size]
            if len(piece) >= 2:
                work.append(piece)

    for members in work:
        block_texts = [texts[i] for i in members]
        if not any(len(t.strip()) > 30 for t in block_texts):
            continue

        # use_idf=False: IDF được tính RIÊNG trong từng ô nên cùng một ngưỡng cosine
        # mang nghĩa khác nhau tuỳ mật độ ô (IDF của cụm từ rao phổ biến lệch nhiều lần
        # giữa ô 2 tin và ô 300 tin). Bỏ IDF thì ngưỡng 0,85 có một nghĩa duy nhất trên
        # toàn bộ dữ liệu, và còn rẻ hơn hiện tại.
        vectoriser = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=1, use_idf=False
        )
        try:
            matrix = vectoriser.fit_transform(block_texts)
        except ValueError:
            continue
        similarity = cosine_similarity(matrix)

        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                if similarity[a, b] < text_threshold:
                    continue
                price_a, price_b = prices[members[a]], prices[members[b]]
                if np.isfinite(price_a) and np.isfinite(price_b) and max(price_a, price_b) > 0:
                    if abs(price_a - price_b) / max(price_a, price_b) > price_tolerance:
                        continue
                union(members[a], members[b])
                if len(samples) < 50:
                    samples.append(
                        {
                            "cosine": round(float(similarity[a, b]), 3),
                            "id_a": frame.iloc[members[a]]["listing_id"],
                            "id_b": frame.iloc[members[b]]["listing_id"],
                            "gia_a": price_a,
                            "gia_b": price_b,
                            "tieu_de_a": str(frame.iloc[members[a]]["title"])[:70],
                            "tieu_de_b": str(frame.iloc[members[b]]["title"])[:70],
                        }
                    )

    groups: dict[int, list[int]] = defaultdict(list)
    for position in range(len(frame)):
        groups[find(position)].append(position)
    return [members for members in groups.values() if len(members) > 1], samples, block_stats


def deduplicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bỏ bản đăng lại, giữ bản mới nhất (hoà thì giữ bản mô tả dài nhất).

    Cột `duplicate_group` được giữ lại: nếu về sau muốn chia tập theo nhóm thay vì loại
    hẳn bản trùng thì đã có sẵn khoá nhóm, không phải tính lại.
    """
    frame = frame.reset_index(drop=True)
    groups, samples, block_stats = find_duplicate_groups(frame)

    published = pd.to_datetime(frame["published_at"], errors="coerce", utc=True)
    length = frame["description"].fillna("").str.len()

    drop: list[int] = []
    group_id = pd.Series(pd.NA, index=frame.index, dtype="object")

    for number, members in enumerate(groups):
        ranked = sorted(
            members,
            key=lambda i: (
                published.iloc[i] if pd.notna(published.iloc[i]) else pd.Timestamp.min.tz_localize("UTC"),
                length.iloc[i],
            ),
            reverse=True,
        )
        for position in members:
            group_id.iloc[position] = f"g{number}"
        drop.extend(ranked[1:])

    kept = frame.drop(index=drop).reset_index(drop=True)
    stats = {
        "nhóm trùng": len(groups),
        "dòng bị loại": len(drop),
        # Funnel phải nói thật về phần dữ liệu được xử lý khác thường, nếu không thì
        # "đã quét mọi ô" là một câu không ai kiểm được.
        **block_stats,
        "mẫu cặp để rà tay": samples,
    }
    kept["duplicate_group"] = group_id.drop(index=drop).reset_index(drop=True)
    return kept, stats
