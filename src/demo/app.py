"""T5.1 và T5.2 — web app demo bằng Streamlit.

    streamlit run src/demo/app.py

App nạp đúng artefact `models/champion.joblib` mà bước huấn luyện xuất ra, nên con số
hiện trên màn hình luôn khớp với con số trong báo cáo. Không có nhánh code riêng cho
demo: mọi biến đổi đặc trưng đi qua cùng một pipeline đã fit.

Khoảng tin cậy lấy từ MdAPE đo trên hold-out chứ không phải một con số tự đặt. Hiện một
giá duy nhất cho bài toán có sai số trung vị hai chữ số là làm người dùng hiểu sai mức
chắc chắn của mô hình.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from src import config
from src.features.build import build_feature_frame
from src.features.text import pretokenize
from src.preprocess.leakage import strip_price_mentions

MODEL_PATH = config.ROOT / "models" / "champion.joblib"
ERROR_PATH = config.REPORTS / "results" / "error_analysis.json"
BILLION = 1e9


@st.cache_resource
def load_artifacts() -> tuple[dict, dict]:
    if not MODEL_PATH.exists():
        st.error(
            f"Chưa có mô hình tại `{MODEL_PATH}`. Chạy `make train` rồi "
            "`python -m src.evaluation.analysis` trước."
        )
        st.stop()
    bundle = joblib.load(MODEL_PATH)
    errors = json.loads(ERROR_PATH.read_text(encoding="utf-8")) if ERROR_PATH.exists() else {}
    return bundle, errors


@st.cache_data
def load_reference() -> pd.DataFrame:
    path = config.DATA_PROCESSED / "listings.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(
        path, columns=["district", "ward", "property_type", "legal_status", "direction", "position"]
    )


def build_input_row(values: dict) -> pd.DataFrame:
    """Dựng một dòng đúng lược đồ mà `build_feature_frame` mong đợi."""
    description = values["description"] or ""
    cleaned = strip_price_mentions(description)
    row = {
        "total_price_vnd": 0.0,  # chỉ để giữ chỗ, không đi vào X
        "area_m2": values["area_m2"],
        "bedrooms": values["bedrooms"],
        "bathrooms": values["bathrooms"],
        "floors": values["floors"],
        "frontage_m": values["frontage_m"],
        "alley_width_m": values["alley_width_m"],
        "bedrooms_missing": 0,
        "bathrooms_missing": 0,
        "floors_missing": 0,
        "frontage_m_missing": 0,
        "alley_width_m_missing": 0,
        "district": values["district"],
        "ward": values["ward"],
        "property_type": values["property_type"],
        "legal_status": values["legal_status"],
        "direction": values["direction"],
        "position": values["position"],
        "published_at": pd.Timestamp.now(tz="UTC"),
        "title": "",
        "description": description,
        "description_clean": cleaned,
        "description_tokens": pretokenize(cleaned),
    }
    return pd.DataFrame([row])


def main() -> None:
    st.set_page_config(page_title="Dự báo giá nhà TP.HCM", page_icon="🏠", layout="wide")
    bundle, errors = load_artifacts()
    reference = load_reference()

    st.title("Dự báo giá nhà TP.HCM từ tin rao")
    st.caption(
        f"Mô hình: **{bundle['model_name']}** · huấn luyện trên "
        f"{bundle['trained_rows']:,} tin".replace(",", ".")
        + " · CS106.F31.CN2 — Nhóm 14"
    )

    districts = sorted(reference["district"].unique()) if len(reference) else config.TARGET_DISTRICTS
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Thông tin bất động sản")
        district = st.selectbox("Quận (hệ cũ)", districts,
                                index=districts.index("Tân Bình") if "Tân Bình" in districts else 0)
        wards = (
            sorted(reference.loc[reference["district"] == district, "ward"].unique())
            if len(reference) else ["không rõ"]
        )
        ward = st.selectbox("Phường", wards)
        property_type = st.selectbox(
            "Loại bất động sản",
            sorted(reference["property_type"].unique()) if len(reference) else ["Nhà"],
        )

        col1, col2 = st.columns(2)
        area = col1.number_input("Diện tích (m²)", 10.0, 1000.0, 60.0, step=5.0)
        floors = col2.number_input("Số tầng", 1, 10, 3)
        bedrooms = col1.number_input("Số phòng ngủ", 1, 15, 3)
        bathrooms = col2.number_input("Số nhà tắm", 1, 15, 2)
        frontage = col1.number_input("Mặt tiền (m)", 1.5, 30.0, 4.0, step=0.5)
        alley = col2.number_input("Bề rộng hẻm (m)", 0.0, 20.0, 5.0, step=0.5)

        position = st.radio("Vị trí", ["hẻm", "mặt tiền", "không rõ"], horizontal=True)
        legal = st.selectbox(
            "Pháp lý",
            sorted(reference["legal_status"].unique()) if len(reference) else ["sổ hồng"],
        )
        direction = st.selectbox(
            "Hướng",
            sorted(reference["direction"].unique()) if len(reference) else ["không rõ"],
        )
        description = st.text_area(
            "Mô tả tin rao",
            "Nhà đẹp hẻm xe hơi, sổ hồng riêng, full nội thất, gần chợ và trường học, vào ở ngay.",
            height=140,
            help="Mọi con số tiền trong mô tả sẽ bị xoá trước khi đưa vào mô hình.",
        )
        predict = st.button("Dự báo giá", type="primary", use_container_width=True)

    with right:
        st.subheader("Kết quả")
        if not predict:
            st.info("Nhập thông tin bên trái rồi bấm **Dự báo giá**.")
            return

        row = build_input_row(
            {
                "district": district, "ward": ward, "property_type": property_type,
                "area_m2": area, "floors": floors, "bedrooms": bedrooms,
                "bathrooms": bathrooms, "frontage_m": frontage, "alley_width_m": alley,
                "position": position, "legal_status": legal, "direction": direction,
                "description": description,
            }
        )
        features = build_feature_frame(row)[bundle["feature_columns"]]
        prediction = float(bundle["pipeline"].predict(features)[0])

        mdape = errors.get("overall", {}).get("MdAPE (%)", 20.0)
        low, high = prediction * (1 - mdape / 100), prediction * (1 + mdape / 100)

        st.metric("Giá ước lượng", f"{prediction / BILLION:,.2f} tỷ đồng".replace(",", "."))
        st.write(
            f"Khoảng tham khảo: **{low / BILLION:.2f} – {high / BILLION:.2f} tỷ**  \n"
            f"Khoảng này rộng bằng sai số phần trăm trung vị đo trên tập hold-out "
            f"({mdape:.1f}%), không phải một con số tự đặt.".replace(".", ",", 1)
        )
        st.caption(
            f"Đơn giá tương ứng: {prediction / area / 1e6:,.1f} triệu đồng/m²".replace(",", ".")
        )

        with st.expander("Vì sao mô hình cho ra con số này?", expanded=True):
            render_explanation(bundle["pipeline"], features)

        st.warning(
            "Mô hình học từ **giá rao**, không phải giá giao dịch. Dùng để tham khảo mặt "
            "bằng rao bán, không dùng cho quyết định tài chính."
        )


def render_explanation(pipeline, features: pd.DataFrame) -> None:
    """Panel giải thích SHAP cho đúng dự báo vừa chạy (T5.2)."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import shap
    except ImportError:
        st.info("Chưa cài shap/matplotlib nên chưa hiện được phần giải thích.")
        return

    try:
        transformer = pipeline.named_steps["features"]
        matrix = transformer.transform(features)
        names = list(transformer.get_feature_names_out())
        model = pipeline.named_steps["model"].regressor_

        explainer = shap.Explainer(model, feature_names=names)
        values = explainer(matrix, check_additivity=False)

        figure = plt.figure()
        shap.plots.waterfall(values[0], max_display=12, show=False)
        st.pyplot(figure, use_container_width=True)
        plt.close(figure)
        st.caption(
            "Mỗi thanh là mức một đặc trưng đẩy dự báo lên hay xuống, tính trên thang "
            "log(giá). Thanh dài nhất là yếu tố quyết định nhiều nhất cho chính căn này."
        )
    except Exception as exc:  # noqa: BLE001
        st.info(f"Không dựng được biểu đồ giải thích cho ca này: {exc}")


if __name__ == "__main__":
    main()
