import re
import smtplib
import socket

import dns.resolver

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

DISPOSABLE_DOMAINS = {"mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com"}


def validate_syntax(email: str) -> tuple[bool, str | None]:
    if EMAIL_RE.match(email):
        return True, None
    return False, "Invalid email format"


def validate_mx(domain: str) -> tuple[bool, str | None]:
    try:
        records = dns.resolver.resolve(domain, "MX", lifetime=5)
        if records:
            return True, None
        return False, "No MX records found"
    except dns.resolver.NXDOMAIN:
        return False, "Domain does not exist"
    except dns.resolver.NoAnswer:
        return False, "No MX records found"
    except dns.resolver.NoNameservers:
        return False, "DNS servers unavailable"
    except (dns.resolver.LifetimeTimeout, dns.exception.Timeout):
        return True, None
    except Exception:
        return True, None


def get_mx_host(domain: str) -> str | None:
    try:
        records = dns.resolver.resolve(domain, "MX", lifetime=5)
        best = sorted(records, key=lambda r: r.preference)
        return str(best[0].exchange).rstrip(".")
    except Exception:
        return None


def validate_smtp(email: str, mx_host: str) -> tuple[bool | None, str | None]:
    """
    Returns (is_valid, reason):
      - (True,  None)   — server accepted (250)
      - (False, reason) — server explicitly rejected (5xx on RCPT TO)
      - (None,  reason) — could not determine (timeout, 4xx, blocked port 25, etc.)
    """
    try:
        with smtplib.SMTP(mx_host, 25, timeout=8) as smtp:
            smtp.ehlo("check.local")
            smtp.mail("verify@check.local")
            code, _ = smtp.rcpt(email)
            if code == 250:
                return True, None
            if 500 <= code < 600:
                return False, f"SMTP rejected: code {code}"
            return None, f"SMTP inconclusive: code {code}"
    except smtplib.SMTPServerDisconnected:
        return None, "SMTP server disconnected"
    except (socket.timeout, TimeoutError):
        return None, "SMTP connection timed out"
    except ConnectionRefusedError:
        return None, "SMTP port 25 blocked"
    except OSError as e:
        return None, f"SMTP network error: {e}"
    except Exception as e:
        return None, f"SMTP error: {str(e)}"


def validate_email_full(email: str, strict_smtp: bool = False) -> tuple[bool, str | None]:
    """
    Three-stage validation.

    When `strict_smtp=False` (default), only explicit 5xx RCPT TO rejections
    mark the address as invalid. Timeouts, blocked ports, or 4xx results are
    treated as "undetermined" and the address is accepted as valid so that
    cloud-provider restrictions (blocked port 25, missing PTR record) don't
    prevent sending to real mailboxes.
    """
    ok, err = validate_syntax(email)
    if not ok:
        return False, err

    domain = email.split("@")[1].lower()
    if domain in DISPOSABLE_DOMAINS:
        return False, "Disposable email domain"

    ok, err = validate_mx(domain)
    if not ok:
        return False, err

    mx_host = get_mx_host(domain)
    if not mx_host:
        return True, None

    smtp_result, smtp_err = validate_smtp(email, mx_host)

    if smtp_result is False:
        return False, smtp_err

    if strict_smtp and smtp_result is None:
        return False, smtp_err

    return True, None
