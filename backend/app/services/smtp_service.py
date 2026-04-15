import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def test_smtp_connection(
    host: str, port: int, login: str, password: str, use_tls: bool
) -> tuple[bool, str]:
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()

        server.login(login, password)
        server.quit()
        return True, "Connection successful"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed: wrong login or password"
    except smtplib.SMTPConnectError as e:
        return False, f"Could not connect to SMTP server: {e}"
    except Exception as e:
        return False, f"SMTP error: {str(e)}"


def send_email(
    host: str,
    port: int,
    login: str,
    password: str,
    use_tls: bool,
    from_email: str,
    to_email: str,
    subject: str,
    body_html: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=30)
    else:
        server = smtplib.SMTP(host, port, timeout=30)
        server.ehlo()
        if use_tls:
            server.starttls()
            server.ehlo()

    server.login(login, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()
