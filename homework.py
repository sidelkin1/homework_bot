import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import EndpointAccessProblem, TelegramBotError

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(name)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except Exception as error:
        raise TelegramBotError(error) from error
    else:
        logger.info(f"Бот отправил сообщение '{message}'")


def send_messages(bot, messages):
    """Отправляет несколько сообщений в Telegram чат."""
    for message in messages:
        send_message(bot, message)


def send_error(bot, message):
    """Отправляет сообщение об ошибке в Telegram чат."""
    try:
        send_message(bot, message)
    except Exception as error:
        message = f'Сбой в работе программы: {error}'
        logger.error(message)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    logger.info(f"Делаем запрос к сервису API '{ENDPOINT}'")
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise EndpointAccessProblem(response.url, response.status_code)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    logger.info('Проверяем ответ API на корректность')
    if not isinstance(response, dict):
        message = (
            f"Неизвестный тип ответа '{type(response)}'. "
            f"Ожидается словарь"
        )
        raise TypeError(message)
    for key in ['homeworks', 'current_date']:
        if key not in response:
            message = f"Отсутствует ожидаемый ключ '{key}' в ответе API"
            raise KeyError(message)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        message = (
            f"Неизвестный тип работ '{type(homeworks)}'. "
            f"Ожидается простой список"
        )
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    for key in ['homework_name', 'status']:
        if key not in homework:
            message = f"Отсутствует ожидаемый ключ '{key}' в работе"
            raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        message = f"Неизвестный статус работы '{homework_status}'"
        raise KeyError(message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует переменная окружения!')
        sys.exit('Программа принудительно остановлена.')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_report = {}
    prev_report = {}

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if homeworks := check_response(response):
                for homework in homeworks:
                    message = parse_status(homework)
                    current_report[homework['homework_name']] = message
                if current_report != prev_report:
                    send_messages(bot, current_report.values())
                    prev_report = current_report.copy()
            else:
                logger.debug('В ответе отсутствуют новые статусы')
            current_timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if not isinstance(error, TelegramBotError):
                current_report['error'] = message
                if current_report != prev_report:
                    send_error(bot, message)
                    prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
