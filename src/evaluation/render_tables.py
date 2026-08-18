"""T4.14 — sinh lại MỌI bảng markdown từ các file kết quả JSON.

Bảng trong báo cáo không bao giờ được gõ tay. Chạy lại script này phải cho ra file
giống hệt byte-to-byte, nhờ vậy con số trong báo cáo luôn truy được về đúng một lần
chạy và không thể lệch giữa báo cáo với slide.

    python -m src.evaluation.render_tables
"""

from __future__ import annotations

import json

from src import config
from src.evaluation.metrics import LOWER_IS_BETTER, METRIC_ORDER
from src.models.registry import TIER_ORDER
from src.utils.logging_setup import get_logger

RESULTS_DIR = config.REPORTS / "results"
TABLES_DIR = config.TABLES


def _tier(label: str) -> str:
    """Chuẩn hoá nhãn tầng đọc từ file kết quả cũ.

    Nhãn tầng từng dùng dấu gạch dài; văn bản của dự án thống nhất không dùng ký tự đó.
    File kết quả sinh trước khi đổi vẫn còn nhãn cũ, nên bước sinh bảng quy đổi tại chỗ
    thay vì bắt chạy lại toàn bộ thí nghiệm chỉ để đổi một ký tự.
    """
    return label.replace(" — ", " · ")


def _vi(value: float, digits: int = 3) -> str:
    """Số theo cách viết Việt Nam: dấu phẩy thập phân.

    Giá trị NaN nghĩa là mô hình không cho ra nổi một dự báo hữu hạn nào. In "nan" vào
    bảng báo cáo thì người đọc tưởng script hỏng; ghi thẳng "tràn số" mới đúng chuyện
    đã xảy ra.
    """
    if value != value:  # NaN
        return "tràn số"
    if value in (float("inf"), float("-inf")):
        return "tràn số"
    return f"{value:.{digits}f}".replace(".", ",")


def _cell(mean: float, std: float, digits: int = 3, bold: bool = False) -> str:
    text = f"{_vi(mean, digits)} ± {_vi(std, digits)}"
    return f"**{text}**" if bold else text


def _best_index(values: list[float], metric: str) -> int:
    if LOWER_IS_BETTER[metric]:
        return min(range(len(values)), key=lambda i: values[i])
    return max(range(len(values)), key=lambda i: values[i])


def render_e1(payload: dict) -> str:
    models = sorted(
        payload["models"],
        key=lambda m: (
            TIER_ORDER.index(_tier(m["tier"])) if _tier(m["tier"]) in TIER_ORDER else 99,
            m["name"],
        ),
    )
    lines = [
        f"# E1: {payload['label']}",
        "",
        f"{payload['n_rows']:,} dòng".replace(",", ".")
        + f", chia hold-out {int((1 - config.HOLDOUT_TEST_SIZE) * 100)}/"
        + f"{int(config.HOLDOUT_TEST_SIZE * 100)}"
        + f", {config.CV_FOLDS}-fold trên phần train, seed {payload['seed']}.",
        f"Ngân sách tinh chỉnh: RandomizedSearch {payload['search_iterations']} cấu hình, "
        "giống nhau cho mọi mô hình.",
        "",
        "Mỗi ô là trung bình ± độ lệch chuẩn qua 5 fold. **In đậm** là tốt nhất mỗi cột.",
        "",
        "| Tầng | Mô hình | " + " | ".join(METRIC_ORDER) + " |",
        "|---|---|" + "---:|" * len(METRIC_ORDER),
    ]

    best = {
        metric: _best_index([m["cv_mean"][metric] for m in models], metric)
        for metric in METRIC_ORDER
    }

    for position, model in enumerate(models):
        cells = []
        for metric in METRIC_ORDER:
            digits = 1 if metric == "MdAPE (%)" else 3
            cells.append(
                _cell(model["cv_mean"][metric], model["cv_std"][metric], digits,
                      bold=(position == best[metric]))
            )
        lines.append(f"| {_tier(model['tier'])} | {model['name']} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Đo trên tập hold-out (chưa từng dùng để chọn tham số)",
        "",
        "| Mô hình | " + " | ".join(METRIC_ORDER) + " |",
        "|---|" + "---:|" * len(METRIC_ORDER),
    ]
    for model in models:
        cells = [
            _vi(model["holdout"][metric], 1 if metric == "MdAPE (%)" else 3)
            for metric in METRIC_ORDER
        ]
        lines.append(f"| {model['name']} | " + " | ".join(cells) + " |")

    # Mô hình nào sinh ra dự báo vô cực thì phải nêu đích danh: chỉ số của nó tính trên
    # phần dự báo hữu hạn, nên không so trực tiếp với các dòng khác được.
    broken = [
        (m["name"], m["cv_mean"].get("n_non_finite", 0))
        for m in models
        if m["cv_mean"].get("n_non_finite", 0) > 0
    ]
    if broken:
        lines += [
            "",
            "**Dự báo tràn số**: "
            + ", ".join(f"{name} ({count:.0f} dự báo/fold)" for name, count in broken)
            + ". Các mô hình này sinh ra giá trị vô cực khi `exp` ngược từ thang log; chỉ",
            "số của chúng tính trên phần dự báo hữu hạn nên không so ngang hàng với các",
            "dòng còn lại được.",
        ]

    # Nhóm tuyến tính hay có std của RMSE lớn hơn cả trung bình; đó là dấu hiệu chứ
    # không phải lỗi, và người đọc bảng cần được cảnh báo ngay dưới bảng.
    unstable = [
        m["name"] for m in models
        if m["cv_std"]["RMSE (tỷ)"] > m["cv_mean"]["RMSE (tỷ)"] * 0.6
    ]
    if unstable:
        lines += [
            "",
            "**Chú ý khi đọc**: " + ", ".join(unstable) + " có độ lệch chuẩn của RMSE lớn",
            "so với chính trung bình của nó. Nguyên nhân là mô hình huấn luyện trên log(giá)",
            "và phép `exp` khuếch đại một vài dự báo ngoại suy xa thành sai số khổng lồ trên",
            "thang VND. Trung vị không bị ảnh hưởng nên MdAPE của các mô hình này vẫn ở mức",
            "khá, và đó chính là lý do bảng báo cả bốn chỉ số thay vì chỉ một.",
        ]

    lines += [
        "",
        "Ghi chú: mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính sau khi đã quy",
        "ngược về thang VND. RMSE và MAE tính bằng tỷ đồng. MdAPE là sai số phần trăm",
        "trung vị. Mọi mô hình dùng CHUNG một bộ fold, nên chênh lệch giữa các dòng không",
        "lẫn chênh lệch giữa các phép chia tập.",
    ]
    return "\n".join(lines) + "\n"


def render_e2(payload: dict) -> str:
    """Bảng chuyển giao, kèm chênh lệch TÍNH RA so với bảng E1 cùng nguồn kiểm.

    Chênh lệch được tính chứ không viết tay: câu "chuyển giao làm sai số tăng lên" chỉ
    đúng nếu con số nói vậy, và hướng của nó phải do dữ liệu quyết định. Nếu về sau dữ
    liệu đổi và chuyển giao hoá ra không tệ hơn, bảng này tự nói điều đó thay vì giữ lại
    một câu khẳng định đã sai.
    """
    reference: dict[str, dict] = {}
    e1_path = RESULTS_DIR / "e1_chotot.json"
    if e1_path.exists():
        e1 = json.loads(e1_path.read_text(encoding="utf-8"))
        reference = {m["name"]: m["cv_mean"] for m in e1["models"]}

    lines = [
        "# E2: chuyển giao theo thời gian",
        "",
        f"Huấn luyện trên {payload['train_rows']:,} tin đăng tới {payload['cutoff']}, ".replace(",", ".")
        + f"kiểm trên {payload['test_rows']:,} tin Chợ Tốt crawl tháng 08/2026.".replace(",", "."),
        "",
        "Cả hai phía đều là GIÁ RAO nên chênh lệch đo được là trôi giá theo thời gian,",
        "không lẫn khoảng cách giữa giá rao và giá giao dịch.",
        "",
        "Cột Δ so với cột cùng tên ở bảng E1 nguồn Chợ Tốt (huấn luyện và kiểm cùng trên",
        "dữ liệu 2026). Δ dương nghĩa là chuyển giao làm sai số xấu đi.",
        "",
        "| Mô hình | " + " | ".join(METRIC_ORDER) + " | Δ MdAPE |",
        "|---|" + "---:|" * (len(METRIC_ORDER) + 1),
    ]

    deltas = []
    overflowed = []
    for model in payload["models"]:
        n_bad = model["transfer"].get("n_non_finite", 0)
        if n_bad:
            overflowed.append((model["name"], n_bad))
        cells = [
            _vi(model["transfer"][metric], 1 if metric == "MdAPE (%)" else 3)
            for metric in METRIC_ORDER
        ]
        base = reference.get(model["name"])
        mdape = model["transfer"]["MdAPE (%)"]
        if base and mdape == mdape:
            delta = mdape - base["MdAPE (%)"]
            deltas.append((model["name"], delta))
            sign = "+" if delta > 0 else ""
            cells.append(f"{sign}{_vi(delta, 1)}")
        elif mdape != mdape:
            cells.append("không tính được")
        else:
            cells.append("(không có mốc)")
        lines.append(f"| {model['name']} | " + " | ".join(cells) + " |")

    if overflowed:
        lines += [
            "",
            "**Dự báo tràn số khi chuyển giao**: "
            + ", ".join(f"{name} ({int(count)} dòng)" for name, count in overflowed)
            + ".",
            "",
            "Đây là kết quả đáng chú ý chứ không phải sự cố kỹ thuật. Hồi quy tuyến tính",
            "không có điều chuẩn, học trên hàng chục nghìn dòng với vài trăm cột, sinh ra hệ",
            "số rất lớn; đem sang một tập có phân phối khác thì dự báo trên thang log vọt lên",
            "tới mức `exp` tràn số thực 64 bit. Ridge, cũng là mô hình tuyến tính nhưng có",
            "điều chuẩn, chuyển giao bình thường. Khoảng cách giữa hai dòng đó chính là giá",
            "trị của điều chuẩn khi phân phối dữ liệu dịch chuyển.",
        ]

    learned = [d for name, d in deltas if name not in ("Dummy (trung vị)",)]
    if learned:
        mean_delta = sum(learned) / len(learned)
        worse = sum(1 for d in learned if d > 0)
        lines += [
            "",
            f"Trung bình các mô hình mất {_vi(abs(mean_delta), 1)} điểm phần trăm MdAPE khi"
            if mean_delta > 0 else
            f"Trung bình các mô hình TỐT LÊN {_vi(abs(mean_delta), 1)} điểm phần trăm MdAPE khi",
            f"chuyển giao ({worse}/{len(learned)} mô hình xấu đi).",
            "",
            "Đây là cái giá của việc dùng một mô hình huấn luyện trên dữ liệu cũ cho thị",
            "trường hiện tại. Cần đọc kèm một cảnh báo: tập huấn luyện và tập kiểm không chỉ",
            "khác nhau về thời gian mà còn khác nhau về SÀN, nên một phần chênh lệch là chênh",
            "giữa hai nguồn chứ không phải trôi giá thuần tuý.",
        ]
    return "\n".join(lines) + "\n"


def render_ablation(payload: dict) -> str:
    rows = payload["rows"]
    baseline = rows[0]["cv_mean"]["MdAPE (%)"]
    lines = [
        "# Ablation: đặc trưng văn bản đáng bao nhiêu?",
        "",
        f"Mô hình: {payload['model']}. Cả bốn cấu hình chạy trên CÙNG một bộ fold và cùng",
        "một ngân sách tinh chỉnh, nên khác biệt duy nhất giữa các dòng là nhánh văn bản.",
        "",
        "| Cấu hình đặc trưng | MdAPE (%) | Δ so với chỉ bảng | RMSE (tỷ) | R² |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        mdape = row["cv_mean"]["MdAPE (%)"]
        delta = mdape - baseline
        sign = "+" if delta > 0 else ""
        lines.append(
            f"| {row['configuration']} | {_vi(mdape, 2)} | {sign}{_vi(delta, 2)} | "
            f"{_vi(row['cv_mean']['RMSE (tỷ)'], 3)} | {_vi(row['cv_mean']['R²'], 3)} |"
        )
    lines += [
        "",
        "Δ âm nghĩa là thêm nhánh đó làm sai số giảm. Đây là con số trả lời trực tiếp câu",
        "hỏi của đề: mô tả rao vặt mang bao nhiêu tín hiệu giá.",
    ]
    return "\n".join(lines) + "\n"


def render_e3(payload: dict) -> str:
    rows = payload["rows"]
    lines = [
        "# E3: giữ lại từng phường làm tập kiểm (leave-one-ward-out)",
        "",
        f"Mô hình: {payload['model']}. Mỗi dòng: bỏ toàn bộ tin của một phường ra khỏi",
        "tập huấn luyện, rồi dự báo đúng phường đó. Đây là phép đo khả năng tổng quát",
        "sang khu vực CHƯA TỪNG THẤY.",
        "",
        "| Phường giữ lại | Số tin kiểm | MdAPE (%) | RMSE (tỷ) | R² |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        m = row["metrics"]
        lines.append(
            f"| {row['ward']} | {row['n_test']} | {_vi(m['MdAPE (%)'], 1)} | "
            f"{_vi(m['RMSE (tỷ)'], 3)} | {_vi(m['R²'], 3)} |"
        )
    if rows:
        values = [row["metrics"]["MdAPE (%)"] for row in rows]
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)) ** 0.5
        lines += ["", f"Trung bình MdAPE: {_vi(mean, 1)}% ± {_vi(std, 1)}."]
    lines += [
        "",
        "Kết quả kém hơn E1 là một phát hiện, không phải một thất bại: nó cho biết mô",
        "hình dựa vào địa bàn đến mức nào, và cảnh báo rằng đem mô hình này sang một",
        "phường chưa có dữ liệu thì sai số sẽ ở mức nào.",
    ]
    return "\n".join(lines) + "\n"


def render_error_analysis(payload: dict) -> str:
    lines = [
        "# Phân tích lỗi theo lát cắt",
        "",
        "Đo trên tập hold-out của nguồn Chợ Tốt, bằng mô hình vô địch của bảng E1.",
        "",
        "## Theo quận",
        "",
        "| Quận | Số tin kiểm | MdAPE (%) |",
        "|---|---:|---:|",
    ]
    for row in payload["by_district"]:
        lines.append(f"| {row['district']} | {row['n']} | {_vi(row['MdAPE (%)'], 1)} |")

    lines += [
        "",
        "## Theo khoảng giá",
        "",
        "| Khoảng giá | Số tin kiểm | MdAPE (%) |",
        "|---|---:|---:|",
    ]
    for row in payload["by_price_bin"]:
        lines.append(f"| {row['bin']} | {row['n']} | {_vi(row['MdAPE (%)'], 1)} |")

    bins = payload["by_price_bin"]
    if len(bins) >= 3:
        worst = max(bins, key=lambda r: r["MdAPE (%)"])
        best = min(bins, key=lambda r: r["MdAPE (%)"])
        lines += [
            "",
            f"Sai số thấp nhất ở khoảng {best['bin']} ({_vi(best['MdAPE (%)'], 1)}%) và cao nhất",
            f"ở khoảng {worst['bin']} ({_vi(worst['MdAPE (%)'], 1)}%). Đây là hình chữ U quen",
            "thuộc của bài toán định giá: phân khúc giữa vừa nhiều mẫu vừa đồng nhất, còn hai",
            "đầu vừa ít mẫu vừa đa dạng: nhà rẻ thường là nhà có vấn đề pháp lý hoặc vị trí",
            "đặc thù, nhà đắt thường là bất động sản dị biệt mà vài chục mẫu không đủ để học.",
        ]
    return "\n".join(lines) + "\n"


def render_learning_curve(payload: dict) -> str:
    points = payload["points"]
    lines = [
        "# Đường cong học",
        "",
        f"Mô hình: {payload['model']}. Mỗi dòng: lấy ngẫu nhiên một phần tập huấn luyện,",
        "huấn luyện lại, đo trên cùng một tập hold-out.",
        "",
        "| Tỷ lệ tập huấn luyện | Số tin | RMSE (tỷ) | MdAPE (%) |",
        "|---:|---:|---:|---:|",
    ]
    for row in points:
        lines.append(
            f"| {int(row['fraction'] * 100)}% | {row['n_train']} | "
            f"{_vi(row['RMSE (tỷ)'], 3)} | {_vi(row['MdAPE (%)'], 1)} |"
        )

    if len(points) >= 2:
        first, last, prev = points[0], points[-1], points[-2]
        gain = prev["MdAPE (%)"] - last["MdAPE (%)"]
        still = gain > 0.3
        lines += [
            "",
            f"Từ {first['n_train']} lên {last['n_train']} tin, MdAPE giảm từ "
            f"{_vi(first['MdAPE (%)'], 1)}% xuống {_vi(last['MdAPE (%)'], 1)}%.",
            "",
            (
                f"**Bước cuối vẫn còn giảm {_vi(gain, 1)} điểm phần trăm**, nghĩa là đường cong "
                "chưa phẳng: thu thập thêm dữ liệu vẫn còn cải thiện được sai số, và đó là chỗ "
                "đáng đầu tư tiếp theo."
                if still else
                "**Bước cuối gần như không giảm nữa**, nghĩa là đường cong đã phẳng: nút thắt "
                "nằm ở chất lượng đặc trưng và nhãn chứ không ở số lượng tin, nên công sức nên "
                "chuyển sang chỗ khác thay vì crawl thêm."
            ),
        ]
    return "\n".join(lines) + "\n"


# Slide chỉ đủ chỗ cho vài dòng, nhưng con số trên slide bắt buộc phải là con số trong
# báo cáo (thầy dễ soi nhất chỗ hai tài liệu làm tròn khác nhau). Bảng rút gọn vì thế
# sinh từ CÙNG file kết quả, chỉ chọn ít dòng hơn và ít cột hơn.
SLIDE_MODELS = [
    "Dummy (trung vị)",
    "Trung vị giá/m² theo nhóm",
    "Ridge",
    "Random Forest",
    "LightGBM",
    "XGBoost",
]


def _leaders(payload: dict) -> list[dict]:
    """Các mô hình không phân biệt được với mô hình tốt nhất bằng dữ liệu hiện có.

    Trả về mọi mô hình có MdAPE trung bình nằm trong một độ lệch chuẩn của mô hình dẫn
    đầu. Slide in đậm CẢ NHÓM này chứ không in đậm một cái: chênh 0,1 điểm giữa hai mô
    hình có độ lệch chuẩn ±1,2 không phải là hơn kém, và chính báo cáo dặn không tuyên
    bố hơn kém khi hai khoảng chồng lấn. In đậm đúng một dòng trên slide là tự vi phạm
    quy tắc mình vừa viết ở chương trước.
    """
    candidates = [m for m in payload["models"] if not m["tier"].startswith("0")]
    best = min(candidates, key=lambda m: m["cv_mean"]["MdAPE (%)"])
    margin = best["cv_std"]["MdAPE (%)"]
    return [
        m for m in candidates
        if m["cv_mean"]["MdAPE (%)"] <= best["cv_mean"]["MdAPE (%)"] + margin
    ]


def render_e1_slide(payload: dict) -> str:
    models = {m["name"]: m for m in payload["models"]}
    leaders = _leaders(payload)
    leader_names = {m["name"] for m in leaders}
    best = min(leaders, key=lambda m: m["cv_mean"]["MdAPE (%)"])

    rows = f"{payload['n_rows']:,}".replace(",", ".")
    lines = [
        "# Kết quả chính (E1)",
        "",
        f"{rows} tin Chợ Tốt · 5-fold · cùng bộ fold, cùng ngân sách tinh chỉnh",
        "",
        "| Mô hình | MdAPE (%) | RMSE (tỷ) | R² |",
        "|---|---:|---:|---:|",
    ]
    for name in SLIDE_MODELS:
        model = models.get(name)
        if not model:
            continue
        label = f"**{name}**" if name in leader_names else name
        lines.append(
            f"| {label} | {_vi(model['cv_mean']['MdAPE (%)'], 1)} | "
            f"{_vi(model['cv_mean']['RMSE (tỷ)'], 2)} | {_vi(model['cv_mean']['R²'], 3)} |"
        )

    baseline = models.get("Trung vị giá/m² theo nhóm")
    if baseline:
        gap = baseline["cv_mean"]["MdAPE (%)"] - best["cv_mean"]["MdAPE (%)"]
        shown = [m["name"] for m in leaders if m["name"] in SLIDE_MODELS]
        who = " và ".join(shown) if len(shown) > 1 else best["name"]
        lines += [
            "",
            f"{who} hơn baseline môi giới khoảng {_vi(gap, 1)} điểm phần trăm MdAPE.",
        ]
        if len(leaders) > 1:
            lines.append(
                "Cách biệt giữa các mô hình in đậm nhỏ hơn độ lệch chuẩn giữa các fold, "
                "nên không chọn ra một mô hình thắng."
            )
    return "\n".join(lines) + "\n"


def render_ablation_slide(payload: dict) -> str:
    rows = payload["rows"]
    baseline = rows[0]["cv_mean"]["MdAPE (%)"]
    lines = [
        "# Ablation: văn bản đáng bao nhiêu?",
        "",
        "| Đặc trưng dùng | MdAPE (%) | Δ |",
        "|---|---:|---:|",
    ]
    for row in rows:
        mdape = row["cv_mean"]["MdAPE (%)"]
        delta = mdape - baseline
        sign = "+" if delta > 0 else ""
        lines.append(
            f"| {row['configuration']} | {_vi(mdape, 2)} | {sign}{_vi(delta, 2)} |"
        )
    lines += ["", "Cùng bộ fold, cùng mô hình, cùng ngân sách. Khác biệt duy nhất là nhánh văn bản."]
    return "\n".join(lines) + "\n"


RENDERERS = {
    "error_analysis": ("error-analysis.md", render_error_analysis),
    "learning_curve": ("learning-curve.md", render_learning_curve),
    "e1_chotot": ("e1-results-chotot.md", render_e1),
    "e1_hf": ("e1-results-hf.md", render_e1),
    "e2": ("e2-results.md", render_e2),
    "e3": ("e3-results.md", render_e3),
    "ablation": ("ablation.md", render_ablation),
}

# Bảng chỉ dùng cho slide, ghi vào thư mục riêng để không lẫn với bảng của báo cáo.
SLIDE_RENDERERS = {
    "e1_chotot": ("slide-e1.md", render_e1_slide),
    "ablation": ("slide-ablation.md", render_ablation_slide),
}


def main() -> None:
    logger = get_logger("render_tables")
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    for key, (filename, renderer) in RENDERERS.items():
        source = RESULTS_DIR / f"{key}.json"
        if not source.exists():
            logger.info("chưa có %s, bỏ qua", source.name)
            continue
        payload = json.loads(source.read_text(encoding="utf-8"))
        (TABLES_DIR / filename).write_text(renderer(payload), encoding="utf-8")
        logger.info("%s → %s", source.name, filename)
        written += 1

    slide_dir = config.REPORTS / "slides" / "tables"
    slide_dir.mkdir(parents=True, exist_ok=True)
    for key, (filename, renderer) in SLIDE_RENDERERS.items():
        source = RESULTS_DIR / f"{key}.json"
        if not source.exists():
            continue
        payload = json.loads(source.read_text(encoding="utf-8"))
        (slide_dir / filename).write_text(renderer(payload), encoding="utf-8")
        logger.info("%s → slides/tables/%s", source.name, filename)
        written += 1

    logger.info("đã sinh %d bảng", written)


if __name__ == "__main__":
    main()
