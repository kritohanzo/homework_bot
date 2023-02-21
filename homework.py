import os
import sys
import logging
import time

import requests
from dotenv import load_dotenv
import telegram

from exceptions import (
    MissingEnvironmentVariables,
    NotAvailableEndpoint,
    RequiredKeysAreMissing,
    MissingHomeworkName,
    MissingHomeworkStatus,
    UnknownHomeworkStatus,
    NoNewStatuses,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(message)s", level=logging.INFO
)
logging.StreamHandler(sys.stdout)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

EXCEPTION_ERROR_MESSAGES = {
    NotAvailableEndpoint: "Эндпоинт недоступен",
    RequiredKeysAreMissing: "Ожидаемые ключи в ответе API не обнаружены",
    MissingHomeworkName: 'Отстствует ключ "homework_name" в ответе API',
    MissingHomeworkStatus: "Отсутствует статус домашней работы",
    UnknownHomeworkStatus: "Получен недокументированный "
                           "статус домашней работы",
}


def check_tokens():
    """Проверяет, что все нужные переменные окружения присутствуют."""
    if not PRACTICUM_TOKEN:
        logging.critical(
            "Отсутствует как минимум PRACTICUM_TOKEN. "
            "Нет смысла продолжать работу дальше."
        )
        raise MissingEnvironmentVariables
    if not TELEGRAM_TOKEN:
        logging.critical(
            "Отсутствует как минимум TELEGRAM_TOKEN. "
            "Нет смысла продолжать работу дальше."
        )
        raise MissingEnvironmentVariables
    if not TELEGRAM_CHAT_ID:
        logging.critical(
            "Отсутствует как минимум TElEGRAM_CHAT_ID. "
            "Нет смысла продолжать работу дальше."
        )
        raise MissingEnvironmentVariables


def send_message(bot, message):
    """Отправляет сообщения через объект бота в диалог с ID из константы."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Сообщение "{message}" успешно отправлено')
    except Exception as error:
        logging.error(f"Ошибка при отправке сообщения: {error}")


def get_api_answer(timestamp):
    """Получает данные с удалённого сервера."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
        if response.status_code != 200:
            raise NotAvailableEndpoint
        response = response.json()
        return response
    except requests.RequestException:
        logging.error(
            "При обработке запроса к API произошло неоднозначное исключение."
        )


def check_response(response):
    """Проверяет, что ответ от сервера поступил в нужном виде."""
    if not isinstance(response, dict):
        raise TypeError("Ответ пришёл не в виде словаря")
    if not isinstance(response.get("homeworks"), list):
        raise TypeError(
            'В ответе API домашки под ключом "homeworks" '
            "данные приходят не в виде списка"
        )
    if "homeworks" not in response or "current_date" not in response:
        raise RequiredKeysAreMissing
    if len(response.get("homeworks")) == 0:
        raise NoNewStatuses


def parse_status(homework):
    """Проверяет, что у домашки изменился вердикт ревьювера."""
    if "homework_name" not in homework:
        raise MissingHomeworkName
    if "status" not in homework:
        raise MissingHomeworkStatus
    if homework.get("status") not in HOMEWORK_VERDICTS:
        raise UnknownHomeworkStatus
    homework_name = homework.get("homework_name")
    verdict = HOMEWORK_VERDICTS.get(homework.get("status"))
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    last_sended_problem_in_tg = "empty var"

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            check_response(api_answer)
            print(api_answer)
            message = parse_status(api_answer.get("homeworks")[0])
            send_message(bot, message)
            timestamp = api_answer.get("current_date")
        except TypeError as error:
            logging.error(error)
            if last_sended_problem_in_tg != error:
                send_message(bot, error)
                last_sended_problem_in_tg = error
        except NoNewStatuses:
            logging.debug("Нет новых статусов в ответах")
        except Exception as error:
            if (
                EXCEPTION_ERROR_MESSAGES[error.__class__]
                in EXCEPTION_ERROR_MESSAGES
            ):
                logging.error(f"{EXCEPTION_ERROR_MESSAGES[error.__class__]}")
                if last_sended_problem_in_tg != error:
                    send_message(
                        bot, EXCEPTION_ERROR_MESSAGES[error.__class__]
                    )
                    last_sended_problem_in_tg = error
            else:
                logging.error(f"Неизвестный сбой в работе программы: {error}")
                if last_sended_problem_in_tg != error:
                    send_message(
                        bot, f"Неизвестный сбой в работе программы: {error}"
                    )
                    last_sended_problem_in_tg = error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
