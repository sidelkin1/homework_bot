class EndpointAccessProblem(Exception):
    """Проблемы с доступом к эндпоинту."""

    pass


class APIUnknownFormat(Exception):
    """Неизвестный формат ответа API."""

    pass


class TelegramBotError(Exception):
    """Ошибка при отправке в Telegram."""

    pass
