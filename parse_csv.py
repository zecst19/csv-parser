import argparse
import csv
import re
import random
import string
from datetime import datetime
from dateutil import relativedelta
from pathlib import Path

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
START_DATE_FORMAT = "%Y-%b-%d"
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}"
TIMEZONE_REGEX = r"\s+([A-Za-z]{3,4}$)"

_uuid_map: dict[str, int] = {}
_uuid_counter = 0

def nothing(value: str) -> str:
    return value

def uuid_to_int(value: str) -> str:
    global _uuid_counter
    if value not in _uuid_map:
        _uuid_counter += 1
        _uuid_map[value] = _uuid_counter
    return str(_uuid_map[value])

def _redact_email(value: str) -> str:
    split = value.split('@', 1)
    user = split[0]
    domain = split[1]
    split2 = domain.split('.', 1)
    org = split2[0]
    tld = split2[1]
    random_user = ''.join(random.choices(string.ascii_lowercase, k=len(user)))
    random_org = ''.join(random.choices(string.ascii_lowercase, k=len(org)))

    return random_user + '@' + random_org + '.' + tld

def _redact_name(value: str) -> str:
    split_names = value.split(' ')
    redacted = []
    for name in split_names:
        redacted.append(''.join(random.choices(string.ascii_lowercase, k=len(name))))

    return ' '.join(redacted)

def redact(value: str) -> str:
    if re.match(EMAIL_REGEX, value):
        return _redact_email(value)
    else:
        return _redact_name(value)



def timestamp_to_date(value: str) -> str:
    tz_reg = re.search(TIMEZONE_REGEX, value)
    if tz_reg:
        value = value[:tz_reg.start()]

    try:
        dt = datetime.strptime(value, DATE_FORMAT)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        ## if conversion fails, return original value
        return value


def clear(value: str) -> str:
    return ""


TRANSFORMS = {
    "uuid_to_int": uuid_to_int,
    "redact": redact,
    "timestamp_to_date": timestamp_to_date,
    "clear": clear,
    "none": nothing,
}

def calculate_tenure(value: str) -> str:
    try:
        start_date = datetime.strptime(value, START_DATE_FORMAT)
    except ValueError:
        raise ValueError("Failed parsing start_date")
    
    now = datetime.now()
    diff = relativedelta.relativedelta(now, start_date)
    
    
    return f"{diff.years} year{'s' if diff.years != 1 else ''}, {diff.months} month{'s' if diff.months != 1 else ''}, {diff.days} day{'s' if diff.days != 1 else ''}"

def resolve_manager_names(rows: list[dict]) -> list[dict]:
    id_to_name = {row["user_id"]: row["name"] for row in rows}
    for row in rows:
        manager_id = row.get("manager_id", "")
        row["manager_name"] = id_to_name.get(manager_id, manager_id)

    return rows

def parse_args():
    parser = argparse.ArgumentParser(description="CSV CLI tool")
    parser.add_argument("-i", "--input", required=True, help="input file name")
    parser.add_argument("-o", "--output", help="output file name", default="new_user_sample.csv")
    parser.add_argument("--columns", nargs="+", help="columns to include with optional transform")
    parser.add_argument("--order", nargs="+", help="column order")
    parser.add_argument("--tenure", action="store_true", help="add tenure column")
    parser.add_argument("--resolve-manager", action="store_true", help="add manager name column column")

    return parser.parse_args()

def transform_csv(
        input_file: str, 
        output_file:str, 
        columns_transform: dict[str, str], 
        order: list[str] | None = None,
        tenure: bool = False,
        resolve_manager: bool = False,
        ):
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(f'{input_file}', 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        input_cols = list(reader.fieldnames or [])
        rows = list(reader)

    for col in columns_transform:
        if col not in input_cols:
            raise ValueError(f"Unkown column: {col}")

    if resolve_manager:
        rows = resolve_manager_names(rows)
        if "manager_name" not in input_cols:
            input_cols.append("manager_name")

    if tenure:
        for row in rows:
            row["tenure"] = calculate_tenure(row["start_date"])
        if "tenure" not in input_cols:
            input_cols.append("tenure")

    if order:
        # append columns not in new order to end 
        missing_cols = [c for c in input_cols if c not in order]
        new_order = order + missing_cols
    else:
        new_order = input_cols

    with open(f'{output_file}', 'w', newline='') as new_file:
        writer = csv.DictWriter(new_file, fieldnames=new_order)
        writer.writeheader()
        for row in rows:
            out_row = {}
            for col in new_order:
                value = row.get(col, "")
                transform_name = columns_transform.get(col, "none")
                fn = TRANSFORMS.get(transform_name.lower())
                if fn is None:
                    raise ValueError(f"Unkown transform: {transform_name}")
                out_row[col] = fn(value)
            writer.writerow(out_row)


def main():

    args = parse_args()

    columns_transform: dict[str, str] = {}
    if args.columns:
        for item in args.columns:
            if ":" in item:
                col, transform = item.split(":", 1)
            else :
                col, transform = item, "none"
            columns_transform[col.strip()] = transform.strip()

    transform_csv(
        args.input, 
        args.output,
        columns_transform, 
        args.order, 
        args.tenure,
        args.resolve_manager,
        )
    
if __name__ == "__main__":
    main()