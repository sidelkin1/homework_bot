class EndpointAccessProblem(Exception):
    """Проблемы с доступом к эндпоинту."""

    MESSAGE = "Эндпоинт '{0}' недоступен. Код ответа API: '{1}'"

    def __init__(self, url, status_code):
        """Инициализация."""
        super().__init__(self.MESSAGE.format(url, status_code))


class TelegramBotError(Exception):
    """Ошибка при отправке в Telegram."""

    MESSAGE = "Ошибка '{0}' при отправке в Telegram"

    def __init__(self, error):
        """Инициализация."""
        super().__init__(self.MESSAGE.format(error))
