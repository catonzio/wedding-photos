import pandas as pd
import yaml
from pathlib import Path

CSV_PATH = "tables.csv"
MEDIA_DIR = Path("static/media")
OUTPUT_PATH = "tables.yaml"


def get_media_files(table_dir: Path) -> list[str]:
    if not table_dir.exists():
        return []
    files = sorted(
        f for f in table_dir.iterdir() if f.name != "cover.jpg" and f.is_file()
    )
    return [f"{table_dir.name}/{f.name}" for f in files]


def main():
    # Read with extra columns to handle rows where the date field contains an
    # unquoted comma (e.g. "Oggi, 4 Luglio 2026").
    df = pd.read_csv(
        CSV_PATH,
        header=None,
        names=["name", "date", "date_extra", "description"],
        on_bad_lines="warn",
    )
    # When date_extra is present and description is NaN, the row had 4 cols:
    # name, date_part1, date_part2, description
    mask = df["date_extra"].notna() & df["description"].isna()
    df.loc[mask, "description"] = df.loc[mask, "date_extra"]
    df.loc[~mask & df["date_extra"].notna(), "date"] = (
        df.loc[~mask & df["date_extra"].notna(), "date"]
        + ", "
        + df.loc[~mask & df["date_extra"].notna(), "date_extra"]
    )
    df = df.drop(columns=["date_extra"])

    tables = []
    for i, row in enumerate(df.itertuples(index=False), start=1):
        table_dir = MEDIA_DIR / f"table_{i}"

        name = row.name if pd.notna(row.name) else ""
        date = str(row.date).strip() if pd.notna(row.date) else None
        description = (
            str(row.description).strip() if pd.notna(row.description) else None
        )

        entry = {
            "id": i,
            "name": name,
        }
        if date:
            entry["date"] = date
        if description:
            entry["description"] = description

        cover_path = f"table_{i}/cover.jpg"
        entry["cover"] = cover_path
        entry["media"] = get_media_files(table_dir)

        tables.append(entry)

    data = {"tables": tables}

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    print(f"Generated {OUTPUT_PATH} with {len(tables)} tables.")


if __name__ == "__main__":
    main()
