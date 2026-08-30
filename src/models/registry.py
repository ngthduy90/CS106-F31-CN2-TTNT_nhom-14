"""T4.2 và T4.4 — danh mục mô hình ba tầng và ngân sách tinh chỉnh.

Đề bài yêu cầu tối thiểu 3 thuật toán; danh mục này chạy 11, xếp thành ba tầng để bảng
kết quả tự kể được một câu chuyện thay vì chỉ là một đống số:

- **Tầng 0 (mốc)**: Dummy neo R² = 0. Baseline "môi giới" — trung vị giá/m² theo (quận,
  phường, loại nhà) nhân diện tích — là mốc thật sự đáng quan tâm: nó là cách định giá
  mà một người môi giới làm trong đầu, và mọi mô hình học máy phải thắng được nó thì
  công sức mới có nghĩa.
- **Tầng 1 (tuyến tính)**: Linear / Ridge / Lasso. Ridge bắt buộc có khi ghép TF-IDF
  nghìn chiều; Lasso cho ra bảng hệ số khác 0 rất dễ đọc.
- **Tầng 2 (chủ lực)**: RandomForest, LightGBM, CatBoost — nhóm mạnh nhất cho dữ liệu
  bảng cỡ này.
- **Tầng 3 (mở rộng)**: KNN (trực giác "so nhà tương tự"), cây quyết định đơn (vẽ được
  luật định giá), MLP (đại diện mạng nơ-ron).

Ngân sách tinh chỉnh là `config.SEARCH_ITERATIONS` lượt RandomizedSearch, cùng seed cho
mọi mô hình — nhưng lượt rút thật sự là **min(ngân sách, kích thước lưới)**: lưới rời rạc
nhỏ hơn ngân sách thì search không thể rút quá số cấu hình đang có (MLP 9, KNN 10, cây
quyết định 20, so với 40 của RF/LightGBM/CatBoost). Nói "ngân sách giống nhau" mà không
nói điều này là để bảng so sánh ngầm hiểu sai. `ModelSpec.grid_size` ghi lại con số thật
cho từng mô hình để báo cáo trích được đúng thứ đã chạy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.tree import DecisionTreeRegressor

from src import config


class GroupMedianRegressor(BaseEstimator, RegressorMixin):
    """Baseline "môi giới": trung vị giá/m² của nhóm × diện tích.

    Không phải mô hình học máy, và đó chính là điểm của nó. Nếu LightGBM chỉ nhỉnh hơn
    cách tính này vài phần trăm thì phần lớn giá trị nằm ở dữ liệu địa bàn chứ không
    nằm ở mô hình — một kết luận đáng viết vào báo cáo hơn bất kỳ con số R² nào.

    Nhận thẳng DataFrame thô (không qua ColumnTransformer) vì nó cần đọc tên quận,
    phường, loại nhà và diện tích ở dạng nguyên bản.
    """

    def __init__(self, group_columns=("district", "ward", "property_type"), area_column="area_m2"):
        self.group_columns = list(group_columns)
        self.area_column = area_column

    def fit(self, X: pd.DataFrame, y):
        frame = X.copy()
        frame["_unit_price"] = np.asarray(y, dtype="float64") / frame[self.area_column].to_numpy()

        self.global_unit_price_ = float(np.nanmedian(frame["_unit_price"]))
        self.levels_ = []
        # Nhóm hẹp trước, nhóm rộng sau: (quận, phường, loại) → (quận, phường) → (quận).
        for depth in range(len(self.group_columns), 0, -1):
            keys = self.group_columns[:depth]
            self.levels_.append((keys, frame.groupby(keys)["_unit_price"].median()))
        return self

    def predict(self, X: pd.DataFrame):
        area = X[self.area_column].to_numpy(dtype="float64")
        unit = np.full(len(X), np.nan)

        for keys, table in self.levels_:
            missing = np.isnan(unit)
            if not missing.any():
                break
            index = pd.MultiIndex.from_frame(X.loc[missing, keys]) if len(keys) > 1 else X.loc[missing, keys[0]]
            unit[missing] = table.reindex(index).to_numpy()

        unit = np.where(np.isnan(unit), self.global_unit_price_, unit)
        return unit * area


@dataclass
class ModelSpec:
    name: str
    tier: str
    estimator: Any
    param_distributions: dict = field(default_factory=dict)
    needs_raw_frame: bool = False
    notes: str = ""
    # Estimator đơn luồng thì song song hoá duy nhất còn lại là ở vòng search; estimator
    # đã tự dùng hết lõi (RF/LightGBM/CatBoost/XGBoost) thì để 1 để khỏi tranh lõi.
    search_n_jobs: int = 1

    @property
    def grid_size(self) -> int | None:
        """Số cấu hình RỜI RẠC của lưới, hoặc None khi lưới là phân phối liên tục."""
        total = 1
        for values in self.param_distributions.values():
            try:
                total *= len(values)
            except TypeError:
                return None
        return total if self.param_distributions else 0

    def search_budget(self, requested: int) -> int:
        """Số lượt rút THẬT: search không rút quá số cấu hình đang có."""
        grid = self.grid_size
        return requested if grid is None else min(requested, grid)


def build_registry(fast: bool = False) -> list[ModelSpec]:
    """Danh mục mô hình. `fast=True` rút gọn để chạy thử (smoke test), không để báo cáo."""
    seed = config.SEED
    n_jobs = -1

    specs = [
        ModelSpec(
            "Dummy (trung vị)",
            "0 · mốc",
            DummyRegressor(strategy="median"),
            notes="neo R² = 0",
        ),
        ModelSpec(
            "Trung vị giá/m² theo nhóm",
            "0 · mốc",
            GroupMedianRegressor(),
            needs_raw_frame=True,
            notes="baseline môi giới",
        ),
        ModelSpec("Hồi quy tuyến tính", "1 · tuyến tính", LinearRegression()),
        ModelSpec(
            "Ridge",
            "1 · tuyến tính",
            Ridge(random_state=seed),
            {"model__regressor__alpha": np.logspace(-3, 3, 25)},
        ),
        ModelSpec(
            "Lasso",
            "1 · tuyến tính",
            Lasso(random_state=seed, max_iter=5_000),
            {"model__regressor__alpha": np.logspace(-4, 1, 25)},
        ),
        ModelSpec(
            "Random Forest",
            "2 · chủ lực",
            RandomForestRegressor(random_state=seed, n_jobs=n_jobs),
            {
                "model__regressor__n_estimators": [200, 300, 400, 500],
                "model__regressor__max_depth": [None, 12, 18, 24],
                "model__regressor__min_samples_leaf": [1, 2, 4, 8],
                "model__regressor__max_features": ["sqrt", 0.3, 0.5],
            },
        ),
        ModelSpec(
            "K láng giềng",
            "3 · mở rộng",
            KNeighborsRegressor(n_jobs=n_jobs),
            {
                "model__regressor__n_neighbors": [3, 5, 8, 12, 20],
                "model__regressor__weights": ["uniform", "distance"],
            },
            notes="minh hoạ curse of dimensionality",
        ),
        ModelSpec(
            "Cây quyết định",
            "3 · mở rộng",
            DecisionTreeRegressor(random_state=seed),
            {"model__regressor__max_depth": [4, 6, 8, 12, None],
             "model__regressor__min_samples_leaf": [1, 5, 20, 50]},
            notes="vẽ được luật định giá",
        ),
    ]

    try:
        from lightgbm import LGBMRegressor

        specs.append(
            ModelSpec(
                "LightGBM",
                "2 · chủ lực",
                LGBMRegressor(random_state=seed, n_jobs=n_jobs, verbose=-1),
                {
                    "model__regressor__n_estimators": [300, 500, 800],
                    "model__regressor__learning_rate": [0.02, 0.05, 0.1],
                    "model__regressor__num_leaves": [15, 31, 63, 127],
                    "model__regressor__subsample": [0.7, 0.85, 1.0],
                    "model__regressor__reg_lambda": [0.0, 1.0, 5.0],
                },
            )
        )
    except ImportError:
        pass

    try:
        from catboost import CatBoostRegressor

        specs.append(
            ModelSpec(
                "CatBoost",
                "2 · chủ lực",
                CatBoostRegressor(random_state=seed, verbose=0, allow_writing_files=False),
                {
                    "model__regressor__iterations": [300, 600, 900],
                    "model__regressor__learning_rate": [0.03, 0.06, 0.1],
                    "model__regressor__depth": [4, 6, 8],
                },
            )
        )
    except ImportError:
        pass

    try:
        from xgboost import XGBRegressor

        specs.append(
            ModelSpec(
                "XGBoost",
                "2 · chủ lực",
                XGBRegressor(random_state=seed, n_jobs=n_jobs, tree_method="hist"),
                {
                    "model__regressor__n_estimators": [300, 500, 800],
                    "model__regressor__learning_rate": [0.02, 0.05, 0.1],
                    "model__regressor__max_depth": [4, 6, 8, 10],
                    "model__regressor__subsample": [0.7, 0.85, 1.0],
                },
            )
        )
    except ImportError:
        pass

    specs.append(
        ModelSpec(
            "MLP",
            "3 · mở rộng",
            MLPRegressor(random_state=seed, max_iter=400, early_stopping=True),
            {
                "model__regressor__hidden_layer_sizes": [(128,), (256, 64), (128, 64, 32)],
                "model__regressor__alpha": [1e-4, 1e-3, 1e-2],
            },
            notes="dao động theo seed, báo mean±std",
        )
    )

    # Estimator đơn luồng: vòng RandomizedSearch là chỗ song song hoá duy nhất còn lại.
    # Các mô hình cây đã tự chiếm hết lõi nên để n_jobs=1 cho search, tránh tranh lõi.
    single_threaded = {"Linear", "Ridge", "Lasso", "K láng giềng", "Cây quyết định", "MLP"}
    for spec in specs:
        if spec.name in single_threaded:
            spec.search_n_jobs = -1

    if fast:
        keep = {"Dummy (trung vị)", "Trung vị giá/m² theo nhóm", "Ridge", "Random Forest", "LightGBM"}
        specs = [spec for spec in specs if spec.name in keep]

    return specs


TIER_ORDER = ["0 · mốc", "1 · tuyến tính", "2 · chủ lực", "3 · mở rộng"]
