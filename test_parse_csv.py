import csv
import pytest
import parse_csv
from datetime import datetime

@pytest.fixture(autouse=True)
def reset_uuid_state():
    parse_csv._uuid_counter = 0
    parse_csv._uuid_map.clear()
    yield

@pytest.fixture
def mock_csv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "input.csv"
    f.write_text(
        "user_id,manager_id,name,email_address,start_date,last_login\n"
"EFEABEA5-981B-4E45-8F13-425C456BF7F6,CDD3AA5D-F8BF-40BB-B220-36147E1B75F7,Ashley Hernandez,ashley.hernandez@live.com,2025-Mar-01,2025-03-23 16:54:43 CET\n"
"2AB96C22-181C-42DC-8B11-3EDAA281D4F8,A37D98B9-98E7-43ED-9B27-A79EFDDAC033,Lisa Nelson,lisa.nelson@outlook.com,2021-Feb-17,2025-02-27 16:35:22 CET\n"
"0213F1C0-01D9-422C-8737-19FBFA902082,EFEABEA5-981B-4E45-8F13-425C456BF7F6,Amanda Roberts,amanda.roberts@live.com,2020-Jun-19,2025-03-07 17:29:50 CET\n"
    )
    return "input.csv"


def test_timestamp_to_date():
    result = parse_csv.timestamp_to_date("2025-03-23 16:54:43 CET")
    parts = result.split("-")

    assert len(parts) == 3
    assert parts[0] == "2025"
    assert parts[1] == "03"
    assert parts[2] == "23"

def test_timestamp_to_date_without_tz():
    result = parse_csv.timestamp_to_date("2025-03-23 16:54:43")

    assert result == "2025-03-23"

def test_timestamp_to_date_other_format():
    result = parse_csv.timestamp_to_date("2025/03/23T16:54:43.12")

    assert result == "2025/03/23T16:54:43.12"

def test_redact_email():
    result = parse_csv.redact("john.smith@gmail.com")

    assert result != "john.smith@gmail.com"
    assert len(result) == len("john.smith@gmail.com")
    assert "@" in result
    assert "." in result

def test_redact_name():
    result = parse_csv.redact("John A. Smith")

    assert result != "John A. Smith"
    assert len(result) == len("John A. Smith")

def test_uuid_to_int():
    result1 = parse_csv.uuid_to_int("EFEABEA5-981B-4E45-8F13-425C456BF7F6")
    result2 = parse_csv.uuid_to_int("2AB96C22-181C-42DC-8B11-3EDAA281D4F8")
    result3 = parse_csv.uuid_to_int("EFEABEA5-981B-4E45-8F13-425C456BF7F6")

    assert result1 != result2
    assert result1 == result3
    assert int(result1) == 1
    assert int(result2) == 2

def test_transform_column_order(mock_csv):
    headers_in = next(csv.reader(open(mock_csv)))

    assert headers_in[0] == "user_id"
    assert headers_in[1] == "manager_id"
    assert headers_in[2] == "name"
    assert headers_in[3] == "email_address"
    assert headers_in[4] == "start_date"
    assert headers_in[5] == "last_login"

    parse_csv.transform_csv(mock_csv, "mock_output.csv", {}, ["name", "email_address", "start_date"])
    headers_out = next(csv.reader(open("mock_output.csv")))

    assert headers_out[0] == "name"
    assert headers_out[1] == "email_address"
    assert headers_out[2] == "start_date"
    assert headers_out[3] == "user_id"
    assert headers_out[4] == "manager_id"
    assert headers_out[5] == "last_login"

def test_transform_column_clear(mock_csv):
    parse_csv.transform_csv(mock_csv, "mock_output.csv", {"email_address": "clear"})
    rows = list(csv.DictReader(open("mock_output.csv")))

    assert rows[0]["email_address"] == ""
    assert rows[1]["email_address"] == ""
    assert rows[2]["email_address"] == ""

def test_transform_uuid_to_int(mock_csv):
    parse_csv.transform_csv(mock_csv, "mock_output.csv", {"user_id": "uuid_to_int", "manager_id": "uuid_to_int"})
    rows = list(csv.DictReader(open("mock_output.csv")))

    assert rows[0]["user_id"] == "1"
    assert rows[0]["manager_id"] == "2"
    assert rows[1]["user_id"] == "3"
    assert rows[1]["manager_id"] == "4"
    assert rows[2]["user_id"] == "5"
    assert rows[2]["manager_id"] == "1"


def test_transform_timestamp_to_date(mock_csv):
    parse_csv.transform_csv(mock_csv, "mock_output.csv", {"last_login": "timestamp_to_date"})
    rows_out = list(csv.DictReader(open("mock_output.csv")))

    assert rows_out[0]["last_login"] == "2025-03-23"
    assert rows_out[1]["last_login"] == "2025-02-27"
    assert rows_out[2]["last_login"] == "2025-03-07"

def test_transform_redact(mock_csv):
    rows_in = list(csv.DictReader(open(mock_csv)))
    name = rows_in[0]["name"]
    email = rows_in[0]["email_address"]
    parse_csv.transform_csv(mock_csv, "mock_output.csv", {"name": "redact", "email_address": "redact"})
    rows_out = list(csv.DictReader(open("mock_output.csv")))

    assert rows_out[0]["name"] != name
    assert len(rows_out[0]["name"]) == len(name)
    assert rows_out[0]["email_address"] != email
    assert len(rows_out[0]["email_address"]) == len(email)

def test_transform_tenure(mock_csv):
    headers_in = next(csv.reader(open(mock_csv)))

    assert "tenure" not in headers_in

    parse_csv.transform_csv(mock_csv, "mock_output.csv", {}, tenure=True)
    rows_out = list(csv.DictReader(open("mock_output.csv")))

    assert rows_out[0]["tenure"] == "1 year, 0 months, 3 days"
    assert rows_out[1]["tenure"] == "5 years, 0 months, 15 days"
    assert rows_out[2]["tenure"] == "5 years, 8 months, 13 days"

def test_transform_resolve_manager(mock_csv):
    headers_in = next(csv.reader(open(mock_csv)))

    assert "manager_name" not in headers_in

    parse_csv.transform_csv(mock_csv, "mock_output.csv", {}, resolve_manager=True)
    rows_out = list(csv.DictReader(open("mock_output.csv")))

    assert rows_out[2]["manager_name"] == "Ashley Hernandez"

def test_transform_unknown_column(mock_csv):
    with pytest.raises(ValueError, match="Unkown column: unknown_column"):
        parse_csv.transform_csv(mock_csv, "mock_output.csv", {"unknown_column": "redact"})

def test_transform_unknown_transform(mock_csv):
    with pytest.raises(ValueError, match="Unkown transform: unknown_transform"):
        parse_csv.transform_csv(mock_csv, "mock_output.csv", {"name": "unknown_transform"})

def test_file_not_found():
    with pytest.raises(FileNotFoundError, match="Input file not found: unknown_file.csv"):
        parse_csv.transform_csv("unknown_file.csv", "mock_output.csv", {"name": "redact"})