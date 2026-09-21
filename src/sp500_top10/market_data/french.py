"""Market Data: french."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from .transport import retrieve


def download_french_zip_csv(url: str, *, raw_dir: Path | None = None) -> str:
    payload = retrieve(url, raw_dir)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise ValueError(f"Expected one CSV file in {url}, found {csv_members}.")
        raw_text = archive.read(csv_members[0]).decode("utf-8-sig", errors="replace")
    return raw_text


def extract_french_table(
    raw_text: str, date_pattern: str, required_columns: list[str], section_marker: str | None = None
) -> pd.DataFrame:
    lines = raw_text.splitlines()
    search_start = 0
    if section_marker is not None:
        marker_upper = section_marker.upper()
        marker_matches = [i for i, line in enumerate(lines) if marker_upper in line.upper()]
        if not marker_matches:
            raise ValueError(f"French section not found: {section_marker}")
        search_start = marker_matches[0] + 1
    required_upper = {str(column).strip().upper() for column in required_columns}
    header_index = None
    for i in range(search_start, len(lines)):
        header_fields = {
            field.strip().upper() for field in lines[i].split(",")[1:] if field.strip()
        }
        if required_upper.issubset(header_fields):
            header_index = i
            break
    if header_index is None:
        raise ValueError(f"French table header not found for {required_columns}.")
    data_lines = []
    for line in lines[header_index + 1 :]:
        first_field = line.split(",", 1)[0].strip()
        if re.fullmatch(date_pattern, first_field):
            data_lines.append(line)
        elif data_lines:
            break
    if not data_lines:
        raise ValueError("No dated rows found in the selected French table.")
    table_text = "\n".join([lines[header_index]] + data_lines)
    data = pd.read_csv(io.StringIO(table_text), skipinitialspace=True)
    data.columns = [str(column).strip() for column in data.columns]
    data = data.rename(columns={data.columns[0]: "date_code"})
    parsed_lookup = {
        str(column).strip().upper(): column for column in data.columns if column != "date_code"
    }
    missing_columns = [
        column for column in required_columns if str(column).strip().upper() not in parsed_lookup
    ]
    if missing_columns:
        raise ValueError(
            f"French table parsed, but required columns are missing: {missing_columns}. Parsed columns: {data.columns.tolist()}"
        )
    rename_map = {parsed_lookup[str(column).strip().upper()]: column for column in required_columns}
    data = data.rename(columns=rename_map)
    return data


def clean_french_return(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    values = values.mask(values <= -99.0)
    return values / 100
