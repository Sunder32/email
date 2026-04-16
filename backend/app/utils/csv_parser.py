import csv
import io
import re

from openpyxl import load_workbook

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
EMAIL_FIND_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _extract_email(cell) -> str | None:
    """Return cell value as a valid email, or None."""
    if cell is None:
        return None
    value = str(cell).strip().lower()
    if not value:
        return None
    if EMAIL_RE.match(value):
        return value
    match = EMAIL_FIND_RE.search(value)
    return match.group(0).lower() if match else None


def _collect_from_rows(rows) -> list[str]:
    """Walk every cell of every row, keep only valid emails, preserve order, dedupe."""
    seen: set[str] = set()
    emails: list[str] = []
    for row in rows:
        if not row:
            continue
        for cell in row:
            email = _extract_email(cell)
            if email and email not in seen:
                seen.add(email)
                emails.append(email)
    return emails


def parse_emails_from_csv(content: bytes) -> list[str]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    return _collect_from_rows(rows)


def parse_emails_from_xlsx(content: bytes) -> list[str]:
    wb = load_workbook(filename=io.BytesIO(content), read_only=True, data_only=True)
    try:
        rows: list[tuple] = []
        for ws in wb.worksheets:
            rows.extend(ws.iter_rows(values_only=True))
        return _collect_from_rows(rows)
    finally:
        wb.close()


def parse_emails(filename: str, content: bytes) -> list[str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("xlsx", "xls"):
        return parse_emails_from_xlsx(content)
    return parse_emails_from_csv(content)
