import pandas as pd
from pathlib import Path

DATASETS = {
    "dhs_migration": {
        "label": "DHS + Migration only",
        "path":  "data_processing/data/processed/dhs_migration.csv",
    },
    "dhs_arrests": {
        "label": "DHS + Migration + Arrests",
        "path":  "data_processing/data/processed/dhs_arrests.csv",
    },
    "dhs_unrest": {
        "label": 'DHS + Migration + "Arrests" + "Unrest"',
        "path":  "data_processing/data/processed/dhs_unrest.csv",
    },
}

def load_data() -> dict:
    loaded = {}
    for key, meta in DATASETS.items():
        df = pd.read_csv(Path(meta["path"]), parse_dates=["DATE"])
        loaded[key] = df
    return loaded
