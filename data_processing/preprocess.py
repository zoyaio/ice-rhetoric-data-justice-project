from dataclasses import dataclass
from pathlib import Path
import pandas as pd

LOCATION_TYPES = {1: "country", 2: "us_state", 3: "us_city", 4: "world_city", 5: "world_state"}

@dataclass
class Location:
    type: int
    type_label: str
    name: str
    country_code: str
    adm1_code: str
    lat: float
    lon: float
    feature_id: str

def parse_location(loc_str: str):
    parts = loc_str.split("#")
    if len(parts) < 7 or parts[4] == "" or parts[5] == "":
        return None
    loc_type = int(parts[0])
    return Location(
        type=loc_type,
        type_label=LOCATION_TYPES.get(loc_type, "unknown"),
        name=parts[1],
        country_code=parts[2],
        adm1_code=parts[3],
        lat=float(parts[4]),
        lon=float(parts[5]),
        feature_id=parts[6],
    )

def parse_locations(loc_list: list) -> list:
    return [loc for s in loc_list if s and (loc := parse_location(s)) is not None]

DATASETS = {
    "dhs_migration": "data/DHS-MIGRATION.csv",
    "dhs_arrests":   "data/bq-results-ARREST.csv",
    "dhs_unrest":    "data/bq-results-ARREST-UNREST.csv",
}

def process(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["DATE"] = pd.to_datetime(df["DATE"], format="%Y%m%d%H%M%S")
    df["Locations"] = df["Locations"].str.split(";")
    df = df[df["Locations"].apply(lambda s: isinstance(s, list) and len(s) > 0)]
    df["parsed_locations"] = df["Locations"].map(parse_locations)

    exploded = df.explode("parsed_locations").reset_index(drop=True)
    exploded = exploded[exploded["parsed_locations"].apply(
        lambda l: isinstance(l, Location) and l.type in (2, 3) and l.adm1_code != "USDC"
    )]

    return pd.DataFrame({
        "DATE":          exploded["DATE"].values,
        "lat":           exploded["parsed_locations"].apply(lambda l: l.lat).values,
        "lon":           exploded["parsed_locations"].apply(lambda l: l.lon).values,
        "adm1_code":     exploded["parsed_locations"].apply(lambda l: l.adm1_code).values,
        "location_type": exploded["parsed_locations"].apply(lambda l: l.type).values,
    })

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    output_dir = script_dir / "data" / "processed"
    output_dir.mkdir(exist_ok=True)

    for name, relative_path in DATASETS.items():
        csv_path = script_dir / relative_path
        print(f"Processing {csv_path.name}...")
        result = process(csv_path)
        out_path = output_dir / f"{name}.csv"
        result.to_csv(out_path, index=False)
        print(f"  Saved {len(result):,} rows → {out_path}")
