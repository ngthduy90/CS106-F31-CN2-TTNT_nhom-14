PYTHON ?= python

.PHONY: help setup crawl qa prep features train report demo test all clean

help:
	@echo "setup     cài thư viện vào venv hiện tại"
	@echo "crawl     thu thập dữ liệu (Chợ Tốt + mogi) và tải bộ HF"
	@echo "qa        chạy QA gate trên kho thô, xuất bảng kiểm tra"
	@echo "prep      làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ, khử trùng lặp"
	@echo "features  dựng pipeline đặc trưng (bảng + TF-IDF/SVD + cờ văn bản)"
	@echo "train     chạy E1, E2, E3, ablation, SHAP, learning curve"
	@echo "report    sinh lại toàn bộ bảng/hình rồi build báo cáo Word"
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

report:
	$(PYTHON) -m src.evaluation.render_tables
	$(PYTHON) -m src.evaluation.render_figures
	bash scripts/build-docx.sh

demo:
	streamlit run src/demo/app.py

test:
	$(PYTHON) -m pytest -q

all: crawl qa prep features train report

clean:
	rm -rf data/interim/* data/processed/* .pytest_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
