PYTHON ?= python

.PHONY: help setup crawl qa prep features train analysis report members repro submission lock demo test all clean

help:
	@echo "setup     cài thư viện vào venv hiện tại"
	@echo "crawl     thu thập dữ liệu (Chợ Tốt + mogi) và tải bộ HF"
	@echo "qa        chạy QA gate trên kho thô, xuất bảng kiểm tra"
	@echo "prep      làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ, khử trùng lặp"
	@echo "features  dựng pipeline đặc trưng (bảng + TF-IDF/SVD + cờ văn bản)"
	@echo "train     chạy E1, E2, E3, ablation, SHAP, learning curve"
	@echo "analysis  phân tích lỗi, SHAP, learning curve, xuất mô hình vô địch"
	@echo "report    sinh lại toàn bộ bảng/hình rồi build báo cáo Word và slide"
	@echo "members   sinh danh-sach-nhom.xlsx từ config/thanh-vien.yaml"
	@echo "repro     kiểm tra sinh lại bảng và huấn luyện lại ra cùng số"
	@echo "submission ráp thư mục nộp + quét chéo môn + quét dữ liệu lọt"
	@echo "lock      chốt phiên bản thư viện vào requirements-lock.txt"
	@echo "demo      chạy web app Streamlit"
	@echo "test      chạy pytest (bắt buộc gồm test chống leakage)"
	@echo "all       crawl -> qa -> prep -> features -> train -> report"

setup:
	$(PYTHON) -m pip install -r requirements.txt

crawl:
	$(PYTHON) -m src.crawl.run_chotot
	$(PYTHON) -m src.crawl.run_mogi
	$(PYTHON) -m src.crawl.fetch_hf_dataset

qa:
	$(PYTHON) -m src.crawl.qa_gate

prep:
	$(PYTHON) -m src.preprocess.run_pipeline

features:
	$(PYTHON) -m src.features.build

train:
	$(PYTHON) -m src.evaluation.run_experiments

analysis:
	$(PYTHON) -m src.evaluation.analysis

report: analysis
	$(PYTHON) -m src.evaluation.render_tables
	$(PYTHON) scripts/update-readme-metrics.py
	$(PYTHON) -m src.evaluation.render_figures
	bash scripts/build-technical-report.sh
	bash scripts/build-docx.sh
	bash scripts/build-slides.sh

members:
	$(PYTHON) scripts/build-member-list.py

repro:
	$(PYTHON) scripts/check-reproducibility.py

submission: members
	$(PYTHON) scripts/assemble-submission.py

lock:
	$(PYTHON) -m pip freeze > requirements-lock.txt

demo:
	streamlit run src/demo/app.py

test:
	$(PYTHON) -m pytest -q

all: crawl qa prep features train report

clean:
	rm -rf data/interim/* data/processed/* .pytest_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
