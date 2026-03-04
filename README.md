# CSV Transform Tool

A Python command-line application for transforming CSV datasets — reordering columns, applying data transformations, and enriching rows with derived fields.

---

## Requirements

- Python 3.9+
- [python-dateutil](https://pypi.org/project/python-dateutil/)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Files

| File | Description |
|------|-------------|
| `parse_csv.py` | The transform tool |
| `test_parse_csv.py` | pytest test suite |
| `user_sample.csv` | 100-row input dataset |
| `output.csv` | Pre-generated transformed output |

---

## Running the Tool

### Syntax

```bash
python parse_csv.py -i <input> -o <output> [--columns col:transform ...] [--order col ...] [--tenure] [--resolve-manager]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `-i, --input` | True | Input CSV filename |
| `-o, --output` | False | Output CSV filename (default: `new_user_sample.csv`) |
| `--columns` | False | `column:transform` pairs for columns to transform |
| `--order` | False | Desired output column order (unlisted columns are appended at the end) |
| `--tenure` | False | Add a `tenure` column calculated from `start_date` |
| `--resolve-manager` | False | Add a `manager_name` column resolved from `manager_id` |

### Available Transforms

| Transform | Description |
|-----------|-------------|
| `uuid_to_int` | Converts UUIDs to a compact integer sequence, uniqueness preserved |
| `redact` | Replaces names with random same-length strings, emails with random same-structure addresses |
| `timestamp_to_date` | Strips timezone and converts timestamp to `YYYY-MM-DD` |
| `clear` | Replaces the value with an empty string |
| `none` | Passes the value through unchanged (default) |

---

## Command Used to Generate `output.csv`

```bash
python parse_csv.py \
    -i user_sample.csv \
    -o output.csv \
    --columns user_id:uuid_to_int manager_id:uuid_to_int name:redact email_address:redact last_login:timestamp_to_date \
    --tenure \
    --resolve-manager
```

### Per-column effect

| Column | Transform | Input example | Output example |
|--------|-----------|--------------|----------------|
| `user_id` | `uuid_to_int` | `EFEABEA5-981B-4E45-8F13-425C456BF7F6` | `1` |
| `manager_id` | `uuid_to_int` | `CDD3AA5D-F8BF-40BB-B220-36147E1B75F7` | `2` |
| `name` | `redact` | `Ashley Hernandez` | `Kxmrnb Jqlzoaqew` |
| `email_address` | `redact` | `ashley.hernandez@live.com` | `xkahzjqbnmrso@wqyp.com` |
| `start_date` | `none` | `2025-Mar-01` | `2025-Mar-01` |
| `last_login` | `timestamp_to_date` | `2025-03-23 16:54:43 CET` | `2025-03-23` |
| `tenure` | N/A | `2025-Mar-01` | `1 year, 0 months, 3 days` |
| `manager_name` | N/A | `CDD3AA5D-...` | `Lisa Nelson` |

---

## Running the Tests

```bash
pip install pytest
pytest test_parse_csv.py -v
```

---

## Decisions & Assumptions

- **`csv` over `pandas`** — The standard library `csv` module was used instead of pandas deliberately. For a 100-row file, pulling in pandas would be a heavy dependency for no practical gain.

- **`python-dateutil` for tenure** — The only external dependency in the project. Used for its `relativedelta` which handles month/year arithmetic correctly. Implementing this behaviour for a feature that wasn't required wasn't worth it in my opition

- **`last_login` format assumed consistent** — The `timestamp_to_date` transform assumes `last_login` is always in `YYYY-MM-DD HH:MM:SS` format with an optional trailing timezone abbreviation. No handling is in place for other timestamp formats on this column. If the format differs, the original value is returned unchanged.

- **UUID uniqueness not validated** — The input data is not checked for duplicate `user_id` values. The `uuid_to_int` transform maintains its own internal map so duplicate UUIDs in the input will correctly map to the same integer, but no warning is raised. The input file does in fact contain duplicate UUIDs.

- **Column transforms are opt-in** — Columns not listed in `--columns` are passed through unchanged rather than being dropped. The thinking here was that silently dropping columns felt more dangerous than silently passing them through.

- **Single command input over interactive CLI** — An earlier design had the tool prompt the user column by column, asking what transform to apply to each. This was scrapped in favour of a single command with all options upfront, as it's much more practical for developers — it can be scripted, repeated, and version controlled, whereas an interactive prompt can't easily be automated, and it's harder to implement without any gain in this case.

- **Single transform per column** — The `column:transform` format was chosen over a `column:[transform1,transform2]` chained approach. Looking at the data, no column type needed more than one transform applied to it, so the added complexity of chaining wasn't justified. It would be a reasonable extension if the use case arose.

---

## AI Disclosure

I used Claude to generate part of this README(not the 'Scaling-up' section), also the changes in commit 199b79d - "code review", though not generated, were suggested by Claude 

---

## Scaling-up

- Using streaming instead of loading the whole file into memory. Right now the only thing preventing rows being processed one at a time is the `--resolve-manager` flag, but since that's one I chose to introduce it could be discarded or run in a separate tool just for that purpose.

- Using Multiprocessing. Using multiple workers to work on chunks of the data parallelly would increase the performance by a good margin. 

- Using Profiling tools. At scale it can be challenging to find exact bottlenecks so using tools like `cProfile` would be a good idea.