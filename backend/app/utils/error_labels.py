"""Human-readable labels for SMTP / validation errors."""


def smtp_error_label(error: str | None) -> str | None:
    if not error:
        return None
    e = error.lower()

    if "authentication" in e or "auth" in e and "fail" in e:
        return "Неверный логин или пароль"
    if "550" in e and ("user" in e or "mailbox" in e or "not found" in e or "unknown" in e):
        return "Адрес не существует"
    if "550" in e:
        return "Сервер отклонил письмо (550)"
    if "552" in e or "quota" in e or "storage" in e:
        return "Переполнен ящик получателя"
    if "553" in e or "relay" in e:
        return "Сервер не принимает это письмо"
    if "554" in e or "spam" in e or "blocked" in e:
        return "Письмо помечено как спам"
    if "timed out" in e or "timeout" in e:
        return "Таймаут SMTP"
    if "refused" in e or "unreachable" in e:
        return "SMTP-сервер недоступен"
    if "disconnected" in e:
        return "Соединение разорвано"
    if "limit" in e or "too many" in e:
        return "Превышен лимит отправки"
    if "tls" in e or "ssl" in e:
        return "Ошибка TLS/SSL"

    return "Ошибка SMTP"


def validation_error_label(error: str | None) -> str | None:
    if not error:
        return None
    e = error.lower()

    if "format" in e:
        return "Неверный формат"
    if "disposable" in e:
        return "Одноразовый email"
    if "domain does not exist" in e or "nxdomain" in e:
        return "Домен не существует"
    if "mx" in e:
        return "У домена нет почтовых серверов"
    if "smtp rejected" in e:
        return "Сервер отклонил адрес"
    if "smtp" in e:
        return "SMTP не подтвердил адрес"

    return "Не прошёл валидацию"


def validation_category(error: str | None) -> str:
    """Categorize validation error for breakdown statistics."""
    if not error:
        return "other"
    e = error.lower()

    if "format" in e:
        return "syntax_errors"
    if "disposable" in e:
        return "disposable"
    if "domain does not exist" in e or "nxdomain" in e or "mx" in e:
        return "no_mx"
    if "smtp" in e:
        return "smtp_rejected"
    return "other"
