"""Central configuration: paths, source codes, quality thresholds, seed.

Every module imports from here. No other module may hardcode a path or a threshold,
so that a single edit changes the whole pipeline and the report can quote the values.
"""

from pathlib import Path

# --- paths ---------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
DATA_RAW = DATA / "raw"            # immutable crawl output, one file per source per day
DATA_INTERIM = DATA / "interim"    # parsed and cleaned, still per source
DATA_PROCESSED = DATA / "processed"  # model-ready tables
DATA_EXTERNAL = DATA / "external"  # Hugging Face subset, admin mapping tables

REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache"            # geocoding cache, gitignored

# --- reproducibility -----------------------------------------------------

SEED = 42

# --- geography -----------------------------------------------------------
# The project reports in the PRE-2025 administrative frame (district + old ward):
# most historical data uses it, and 168 new wards are too fine for ~10k listings.

TARGET_DISTRICTS = ["Tân Bình", "Tân Phú", "Quận 12"]

# Chợ Tốt gateway codes, verified 2026-08-16 (runbook 01 §3)
CHOTOT_CATEGORY_SALE = 1000        # cg: bất động sản bán
CHOTOT_STATUS_SELLING = "s"        # st
CHOTOT_REGION_HCMC = 13000         # region_v2
CHOTOT_AREA_CODES = {
    "Tân Bình": 13112,
    "Tân Phú": 13113,
    "Quận 12": 13107,
}

# mogi.vn district entry points; the ho-chi-minh prefix is required or the site
# redirects to the nationwide listing (runbook 01 §4)
MOGI_DISTRICT_PATHS = {
    "Tân Bình": "ho-chi-minh/quan-tan-binh/mua-nha-dat",
    "Tân Phú": "ho-chi-minh/quan-tan-phu/mua-nha-dat",
    "Quận 12": "ho-chi-minh/quan-12/mua-nha-dat",
}

# Hugging Face historical source, stands in for the member dataset (execution-plan §2)
HF_DATASET = "tinixai/vietnam-real-estates"
HF_PROVINCE = "Hồ Chí Minh"
HF_CUTOFF = "2025-06-30"           # newest listing date kept for the E2 training side

# --- crawl politeness ----------------------------------------------------

REQUEST_DELAY_SECONDS = 1.5        # runbook 01 §3.5: 1 request per 1–2 seconds
REQUEST_TIMEOUT_SECONDS = 20
MAX_RETRIES = 4
BACKOFF_FACTOR = 2.0
USER_AGENT = (
    "CS106-UIT-student-project/1.0 (academic coursework; contact via GitHub issues)"
)

# --- QA gate (runbook 01 §6) ---------------------------------------------

QA_THRESHOLDS = {
    "min_raw_listings": 8_000,
    "min_share_description_200_chars": 0.90,
    "min_share_numeric_price": 0.80,
    "min_share_ward_or_coords": 0.70,
    "min_listings_target_districts": 3_000,
    "max_pii_matches": 0,
}

# --- cleaning bounds (runbook 02 §3.4, tier 1 hard rules) ----------------
# Starting values only. Tier 2 (IQR on log price per m² per district) derives its
# thresholds from the data itself and overrides these for the final cut.

VALID_AREA_M2 = (10.0, 1_000.0)
VALID_TOTAL_PRICE_VND = (300e6, 100e9)
VALID_FLOORS = (1, 10)
VALID_FRONTAGE_M = (1.5, 20.0)
PRICE_CROSS_CHECK_TOLERANCE = 0.10   # total price vs unit price × area
DUPLICATE_PRICE_TOLERANCE = 0.03     # runbook 02 §3.1
DUPLICATE_TEXT_COSINE = 0.85

# --- modelling (runbook 03) ---------------------------------------------

TARGET_COLUMN = "total_price_vnd"
TARGET_TRANSFORM = "log"             # train on log(price), report on the VND scale
CV_FOLDS = 5
HOLDOUT_TEST_SIZE = 0.20
SEARCH_ITERATIONS = 40               # RandomizedSearch budget, identical per model
PRICE_BINS_VND = [0, 2e9, 5e9, 10e9, float("inf")]  # error analysis slices

# Columns that must never reach the feature matrix: they are the label in disguise.
LEAKAGE_BLOCKLIST = [
    "price_per_m2",
    "price_million_per_m2",
    "unit_price_vnd",
    TARGET_COLUMN,
]
