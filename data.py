import pandas as pd
from pathlib import Path

DATASETS = {
    "dhs_migration": {
        "label": "DHS + Migration only",
        "path":  "data_processing/data/live/dhs_migration.csv",
    },
    "dhs_arrests": {
        "label": "DHS + Migration + Arrests",
        "path":  "data_processing/data/live/dhs_arrests.csv",
    },
    "dhs_unrest": {
        "label": 'DHS + Migration + "Arrests" + "Unrest"',
        "path":  "data_processing/data/live/dhs_unrest.csv",
    },
}

ARRESTS_PATH  = "data_processing/data/live/ice_arrests.csv"
QUOTES_PATH   = "data_processing/data/live/communityQuoteData.csv"
FACEBOOK_PATH = "data_processing/data/live/communityImgData.csv"

def load_data() -> dict:
    loaded = {}
    for key, meta in DATASETS.items():
        df = pd.read_csv(Path(meta["path"]), parse_dates=["DATE"])
        loaded[key] = df
    return loaded

def load_arrests() -> pd.DataFrame:
    return pd.read_csv(Path(ARRESTS_PATH), parse_dates=["date"])

def load_narratives() -> dict:
    quotes = pd.read_csv(Path(QUOTES_PATH))
    posts  = pd.read_csv(Path(FACEBOOK_PATH))
    merged = quotes.merge(posts, on=["city", "org_num"], how="outer")
    merged["city"] = merged["city"].replace("New York", "New York City")
    result = {}
    for city, group in merged.sort_values("org_num").groupby("city"):
        result[city] = group.to_dict("records")
    return result
