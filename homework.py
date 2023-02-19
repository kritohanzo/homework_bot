import os
from telegram.ext import MessageFilter, MessageHandler
from dotenv import load_dotenv
import logging
import telegram
import time
import requests
from exceptions import MissingEnvironmentVariables, ResponseError, NotAvailableEndpoint

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO) 

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    if not PRACTICUM_TOKEN:
        logging.critical('Отсутствует как минимум PRACTICUM_TOKEN. Нет смысла продолжать работу дальше.')
        raise MissingEnvironmentVariables
    if not TELEGRAM_TOKEN:
        logging.critical('Отсутствует как минимум TELEGRAM_TOKEN. Нет смысла продолжать работу дальше.')
        raise MissingEnvironmentVariables
    if not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствует как минимум TElEGRAM_CHAT_ID. Нет смысла продолжать работу дальше.')
        raise MissingEnvironmentVariables


def send_message(bot, message):
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Сообщение "{message}" успешно отправлено')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
        if response.status_code != 200:
            raise NotAvailableEndpoint
        response = response.json()
        return response
    except NotAvailableEndpoint:
        logging.error('Эндпоинт недоступен')
    except Exception as error:
        logging.error(f'Cбои при запросе к эндпоинту: {error}')

def check_response(response):
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error('Ожидаемые ключи в ответе API не обнаружены')
        raise ResponseError


def parse_status(homework):
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    #timestamp = 1642228078

    ...

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            check_response(api_answer)
            send_message(bot, parse_status(api_answer.get('homeworks')[0]))
            timestamp = api_answer.get('current_date')
        except IndexError:
            logging.debug('Нет новых статусов в ответах')
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
