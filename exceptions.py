class EndpointAccessProblem(Exception):
    """Проблемы с доступом к эндпоинту."""

    pass


class APIKeyDoesntExist(Exception):
    """Проблемы с ключами в ответе API."""

    pass


class UnknownHomeworkStatus(Exception):
    """Недокументированный статус домашней работы."""

    pass


class TelegramBotError(Exception):
    """Ошибка при отправке в Telegram."""

    pass


class HomeworkKeyDoesntExist(Exception):
    """Проблемы с ключами в статусе работы."""

    pass
