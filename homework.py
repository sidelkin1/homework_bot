import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (APIKeyDoesntExist, EndpointAccessProblem,
                        TelegramBotError)

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
        msg = f"Ошибка '{error}' при отправке в Telegram"
        raise TelegramBotError(msg) from error
    else:
        logger.info(f"Бот отправил сообщение '{message}'")


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        message = (f"Эндпоинт {response.url} недоступен. "
                   f"Код ответа API: {response.status_code}")
        raise EndpointAccessProblem(message)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        response = response[0]
    for key in ['homeworks', 'current_date']:
        if key not in response:
            message = f"Отсутствует ожидаемый ключ '{key}' в ответе API"
            raise APIKeyDoesntExist(message)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        message = f"Неизвестный тип списка работ {type(homeworks)}"
        raise APIKeyDoesntExist(message)
    return homeworks


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    for key in ['homework_name', 'status']:
        if key not in homework:
            message = f"Отсутствует ожидаемый ключ '{key}' в работе"
            logger.error(message)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        message = f"Неизвестный статус работы '{homework_status}'"
        logger.error(message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    result = True
    tokens_dict = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for name, token in tokens_dict.items():
        if not token:
            message = f"Отсутствует переменная окружения: '{name}'"
            logger.critical(message)
            result = False
    return result


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        print('Программа принудительно остановлена.')
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_error = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.debug('В ответе отсутствуют новые статусы')
            else:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if (not ((old_error == message)
                     or isinstance(error, TelegramBotError))):
                send_message(bot, message)
                old_error = message
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
