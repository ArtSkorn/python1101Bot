import telebot
import requests
from datetime import datetime
import json



TOKEN = "8200923899:AAHbGg7YpnHF7VFSzWEA-TXyhT6MLAMcS6U"

bot = telebot.TeleBot(TOKEN)

DEEPSEEK_API_KEY = "sk-88c71385b6594cfa8a35810243dcecd8"

MAX_TOKENS = 256 #1 СИМВОЛ 0.3 ТОКЕНА

API_URL = "https://api.deepseek.com/v1/chat/completions"

user_usage = {}



#проверка лимитов. Управление к-вом запросов на день
def check_daily_limit(user_id):
    today = datetime.now().date().isoformat()
    #впервые зашел в бота
    if user_id not in user_usage:
        user_usage[user_id] = {'date': today, 'count': 1}
        return True
    #если наступил следующий день, вернуть к-во запросов
    if user_usage[user_id]['date'] != today:
        user_usage[user_id] = {'date': today, 'count': 1},
        return True
    #если лимит исчерпан
    if user_usage[user_id]['count'] >= 10:  # Максимум 10 вопросов в день
        return False
    user_usage[user_id]['count'] += 1
    return True



def deepseekQuestion(question):
    """Запрос к DeepSeek API с оптимизацией токенов"""

    # Обрезаем вопрос если слишком длинный
    if len(question) > 300:
        question = question[:300] + "..."

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Ты полезный помощник. Отвечай максимально кратко и по делу. Ограничь ответ 3-4 предложениями."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "max_tokens": MAX_TOKENS,  # Экономим токены
        "temperature": 0.7,  # Уменьшил температуру для более предсказуемых ответов
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"Ошибка API: {response.status_code}, {response.text}")
            return f"Ошибка: {response.status_code}. Попробуйте позже."

    except requests.exceptions.Timeout:
        return "Время ожидания истекло. Попробуйте снова."
    except Exception as e:
        print(f"Ошибка в askDeepseek: {e}")
        return "Произошла ошибка при обработке запроса."



@bot.message_handler(commands=["start"])
def start(message):
    welcome_text = """ Привет! Я AI-помощник на базе DeepSeek.
    Как использовать:
    • Просто напиши мне вопрос
    • Или используй команду /ai <вопрос>
    Ответы будут краткими и по делу
    Лимит: 10 вопросов в день
    Задавай свой вопрос!"""
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['ai'])
def deepseekSearch(message):
    user_id = message.from_user.id
    # Проверяем лимит
    if not check_daily_limit(user_id):
        bot.send_message(
            message.chat.id,
            " Вы превысили дневной лимит в 10 вопросов. Попробуйте завтра!"
        )
        return
    # Получаем вопрос
    user_question = message.text.replace("/ai", "").strip()
    if not user_question:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, напишите вопрос после команды /ai\nПример: /ai Что такое ИИ?"
        )
        return
    # Отправляем статус "печатает"
    bot.send_chat_action(message.chat.id, 'typing')
    # Получаем ответ от DeepSeek
    deepseekAnswer = deepseekQuestion(user_question)
    # Отправляем ответ
    bot.send_message(message.chat.id, deepseekAnswer)

#@bot.message_handler(commands=["stats"])





bot.infinity_polling()