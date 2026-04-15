import csv
import io
import re

from openpyxl import load_workbook

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def parse_emails_from_csv(content: bytes) -> list[str]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    emails = []
    email_col = None

    for i, row in enumerate(reader):
        if i == 0:
            for j, cell in enumerate(row):
                if cell.strip().lower() in ("email", "e-mail", "mail", "почта", "адрес"):
                    email_col = j
                    break
            if email_col is None:
                for j, cell in enumerate(row):
                    if EMAIL_RE.match(cell.strip()):
                        email_col = j
                        emails.append(cell.strip().lower())
                        break
                if email_col is None:
                    email_col = 0
                    if EMAIL_RE.match(row[0].strip()):
                        emails.append(row[0].strip().lower())
            continue

        if email_col < len(row):
            candidate = row[email_col].strip().lower()
            if candidate and EMAIL_RE.match(candidate):
                emails.append(candidate)

    return emails


def parse_emails_from_xlsx(content: bytes) -> list[str]:
    wb = load_workbook(filename=io.BytesIO(content), read_only=True)
    ws = wb.active
    emails = []
    email_col = None

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            for j, cell in enumerate(row):
                val = str(cell or "").strip().lower()
                if val in ("email", "e-mail", "mail", "почта", "адрес"):
                    email_col = j
                    break
            if email_col is None:
                email_col = 0
            continue

        if email_col < len(row) and row[email_col]:
            candidate = str(row[email_col]).strip().lower()
            if candidate and EMAIL_RE.match(candidate):
                emails.append(candidate)

    wb.close()
    return emails


def parse_emails(filename: str, content: bytes) -> list[str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("xlsx", "xls"):
        return parse_emails_from_xlsx(content)
    return parse_emails_from_csv(content)
