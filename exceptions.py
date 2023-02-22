class NotAvailableEndpoint(Exception):
    """Эндпоинт недоступен."""


class RequiredKeysAreMissing(Exception):
    """Необходимые ключи потеряны."""


class MissingHomeworkName(Exception):
    """Потеряно название домашней работы."""


class MissingHomeworkStatus(Exception):
    """Потерян статус домашней работы."""


class UnknownHomeworkStatus(Exception):
    """Неизвестный статус домашней работы."""


class NoNewStatuses(Exception):
    """Нет новых статусов домашней работы."""


class MessageNotSended(Exception):
    """Сообщение не было отправлено."""


class RequestToAPIError(Exception):
    """При запросе к API произошла ошибка."""
