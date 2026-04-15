import re
import smtplib
import socket

import dns.resolver

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_syntax(email: str) -> tuple[bool, str | None]:
    if EMAIL_RE.match(email):
        return True, None
    return False, "Invalid email format"


def validate_mx(domain: str) -> tuple[bool, str | None]:
    try:
        records = dns.resolver.resolve(domain, "MX")
        if records:
            return True, None
        return False, "No MX records found"
    except dns.resolver.NXDOMAIN:
        return False, "Domain does not exist"
    except dns.resolver.NoAnswer:
        return False, "No MX records found"
    except dns.resolver.NoNameservers:
        return False, "DNS servers unavailable for domain"
    except Exception as e:
        return False, f"MX lookup error: {str(e)}"


def get_mx_host(domain: str) -> str | None:
    try:
        records = dns.resolver.resolve(domain, "MX")
        best = sorted(records, key=lambda r: r.preference)
        return str(best[0].exchange).rstrip(".")
    except Exception:
        return None


def validate_smtp(email: str, mx_host: str) -> tuple[bool, str | None]:
    try:
        with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
            smtp.ehlo("check.local")
            smtp.mail("verify@check.local")
            code, _ = smtp.rcpt(email)
            if code == 250:
                return True, None
            return False, f"SMTP rejected: code {code}"
    except smtplib.SMTPServerDisconnected:
        return False, "SMTP server disconnected"
    except socket.timeout:
        return False, "SMTP connection timed out"
    except Exception as e:
        return False, f"SMTP error: {str(e)}"


def validate_email_full(email: str) -> tuple[bool, str | None]:
    ok, err = validate_syntax(email)
    if not ok:
        return False, err

    domain = email.split("@")[1]

    ok, err = validate_mx(domain)
    if not ok:
        return False, err

    mx_host = get_mx_host(domain)
    if not mx_host:
        return False, "Could not resolve MX host"

    ok, err = validate_smtp(email, mx_host)
    return ok, err
