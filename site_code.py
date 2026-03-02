import json
from pathlib import Path
import pandas as pd

# ===== CONFIG =====
INPUT_FILE = "ALL_SITES.xlsx"  # or ALL_SITES.csv
OUT_DATA = Path("data.js")

COLS = ["MAIN REGION", "SUB REGION", "CLUSTER", "SITE ID", "LAT", "LON", "BAND", "SECTOR", "PCI", "AZIMUTH"]
EMPTY_CLUSTER_NAME = "SSV"
# ================


def read_input(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p.resolve()}")

    if p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(p)
    elif p.suffix.lower() in [".csv", ".txt"]:
        df = pd.read_csv(p)
    else:
        raise ValueError("Unsupported file type. Use .xlsx/.xls or .csv")

    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}\nFound: {list(df.columns)}")

    return df[COLS].copy()


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    # strip text fields
    for c in ["MAIN REGION", "SUB REGION", "CLUSTER", "SITE ID", "BAND", "SECTOR"]:
        df[c] = df[c].astype(str).str.strip()

    # numeric
    df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["LON"] = pd.to_numeric(df["LON"], errors="coerce")
    df["AZIMUTH"] = pd.to_numeric(df["AZIMUTH"], errors="coerce")
    df["PCI"] = pd.to_numeric(df["PCI"], errors="coerce")

    # empty cluster => SSV
    df["CLUSTER"] = df["CLUSTER"].replace(["", "nan", "None", "NULL", "null"], pd.NA)
    df["CLUSTER"] = df["CLUSTER"].fillna(EMPTY_CLUSTER_NAME)

    # keep only valid rows
    df = df[df["SITE ID"].notna() & (df["SITE ID"].astype(str).str.len() > 0)]
    df = df[df["LAT"].notna() & df["LON"].notna() & df["AZIMUTH"].notna()]
    return df


def to_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "MAIN REGION": str(r["MAIN REGION"]),
            "SUB REGION": str(r["SUB REGION"]),
            "CLUSTER": str(r["CLUSTER"]),
            "SITE ID": str(r["SITE ID"]),
            "LAT": float(r["LAT"]),
            "LON": float(r["LON"]),
            "BAND": str(r["BAND"]).strip().upper(),
            "SECTOR": str(r["SECTOR"]).strip(),
            "PCI": None if pd.isna(r["PCI"]) else int(r["PCI"]),
            "AZIMUTH": float(r["AZIMUTH"]),
        })
    return rows


def write_data_js(rows: list[dict], out_path: Path) -> None:
    payload = {"rows": rows}
    js = "window.GNODEB_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    out_path.write_text(js, encoding="utf-8")


def main():
    df = read_input(INPUT_FILE)
    df = clean_df(df)
    rows = to_rows(df)
    write_data_js(rows, OUT_DATA)

    print("✅ Generated:", OUT_DATA.resolve())
    print("Open index.html (already in your folder) and it will use data.js")
    print("Whenever Excel changes, rerun: python build_data_js.py")


if __name__ == "__main__":
    main()