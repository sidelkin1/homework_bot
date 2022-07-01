class EndpointAccessProblem(Exception):
    """Проблемы с доступом к эндпоинту."""

    MESSAGE = "Эндпоинт '{}' недоступен. Код ответа API: '{}'"

    def __init__(self, url, status_code):
        """Инициализация."""
        super().__init__(self.MESSAGE.format(url, status_code))


class TelegramBotError(Exception):
    """Ошибка при отправке в Telegram."""

    MESSAGE = "Ошибка '{}' при отправке в Telegram"

    def __init__(self, error):
        """Инициализация."""
        super().__init__(self.MESSAGE.format(error))
