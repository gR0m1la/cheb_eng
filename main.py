import os

from flask import Flask, request
import requests
import json
import random

app = Flask(__name__)

# BOT_TOKEN = '7143458358:AAESxL1wBU7B5m7mEaTOK4aRvbLF71TwSxs'
bot_token = os.environ.get('BOT_TOKEN')
# LOCAL_TUNNEL_URL = 'https://rude-houses-sit.loca.lt'
WEBHOOK_URL = f'https://cheb-eng.onrender.com/webhook'

USERS_FILE = 'users.json'

def load_user_data(chat_id):
    try:
        with open(USERS_FILE, 'r') as file:
            users_data = json.load(file)
    except FileNotFoundError:
        return None

    return users_data.get(str(chat_id))

user_data = None

def update_user_data(chat_id, new_data):
    try:
        with open(USERS_FILE, 'r') as file:
            users_data = json.load(file)
    except FileNotFoundError:
        # Если файл не найден, создаем пустой словарь для пользователей
        users_data = {}

    # Обновляем данные пользователя или создаем новую запись, если пользователь новый
    users_data[chat_id] = new_data

    # Сохраняем обновленные данные в файл
    with open(USERS_FILE, 'w') as file:
        json.dump(users_data, file)

# Загрузка данных о темах и словах из JSON-файлов
def load_data():
    with open('topics.json', 'r', encoding='utf-8') as f:
        topics = json.load(f)
    return topics

topics = load_data()

def set_webhook(bot_token, webhook_url):
    url = f'https://api.telegram.org/bot{bot_token}/setWebhook'
    payload = {'url': webhook_url}
    response = requests.post(url, data=payload)
    print(response.text)

def parse_update(update):
    chat_id = update['message']['chat']['id']
    text = update['message']['text']
    return chat_id, text

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    response = requests.post(url, data=payload)
    print(response.text)

def start_menu(chat_id):
    text = "Выберите действие:"
    keyboard = {
        "keyboard": [[{"text": "Начать тест"}], [{"text": "Статистика"}], [{"text": "Настройки"}]],
        "resize_keyboard": True
    }
    payload = {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': json.dumps(keyboard)
    }
    response = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(bot_token), data=payload)
    print(response.text)


def start_test(chat_id, topics):
    # Создаем клавиатуру для выбора темы
    keyboard = {
        "keyboard": [[{"text": topic['title']}] for topic in topics['topics']],
        "resize_keyboard": True
    }

    payload = {
        'chat_id': chat_id,
        'text': "Выберите тему:",
        'reply_markup': json.dumps(keyboard)
    }
    response = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(bot_token), data=payload)
    print(response.text)

thought_word = None

# Функция для обработки выбора темы пользователем
def handle_topic_choice(chat_id, topics, topic_title):
    chosen_topic = None
    for topic in topics['topics']:
        if topic['title'] == topic_title:
            chosen_topic = topic
            break

    if chosen_topic:
        words = chosen_topic['words']
        # Выбираем случайное слово из выбранной темы
        word = random.choice(words)
        global thought_word
        thought_word = word['translation']

        # Отправляем пользователю варианты перевода
        translations = [word['translation'] for word in words]
        random.shuffle(translations)

        # Формируем клавиатуру для вариантов перевода
        keyboard = {
            "keyboard": [[{"text": translation}] for translation in translations],
            "resize_keyboard": True
        }

        payload = {
            'chat_id': chat_id,
            'text': f"Переведите слово: {word['english']}",
            'reply_markup': json.dumps(keyboard)
        }
        response = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(bot_token), data=payload)
        print(response.text)
    else:
        send_message(chat_id, "Пожалуйста, выберите существующую тему.")


def show_statistics(chat_id):
    # Здесь ваша логика для отображения статистики
    pass

def settings_menu(chat_id):
    # Здесь ваша логика для отображения меню настроек
    pass


def handle_translation_attempt(chat_id, correct_translation, user_translation):
    if user_translation == correct_translation:
        send_message(chat_id, "Верно! 👍")
    else:
        send_message(chat_id, f"Неверно. 😔 Правильный перевод: {correct_translation}")

    start_menu(chat_id)


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = request.get_json()
        chat_id, text = parse_update(update)

        global user_data
        user_data = load_user_data(chat_id)

        if text == '/start':
            start_menu(chat_id)
        elif text == 'Начать тест':
            start_test(chat_id, topics)
        elif text == 'Статистика':
            show_statistics(chat_id)
        elif text == 'Настройки':
            settings_menu(chat_id)
        elif text in [topic['title'] for topic in topics['topics']]:
            handle_topic_choice(chat_id, topics, text)
        elif text in [word['translation'] for topic in topics['topics'] for word in topic['words']]:
            print(thought_word)
            print(text)
            handle_translation_attempt(chat_id, thought_word, text)
        else:
            send_message(chat_id, "Простите, я не могу понять ваш запрос.")
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
