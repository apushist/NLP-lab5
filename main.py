import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

API_TOKEN = '8474134455:AAHDplEbZx0cUycxBLNPNKQE9xSMnrnhc7c'
bot = telebot.TeleBot(API_TOKEN)

# Ключ: user_id (int), Значение: список сообщений (list of dict)
conversation_history = {}

def get_user_history(user_id):
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {
                "role": "system", 
                "content": "Ты полезный ассистент. Отвечай на вопросы пользователя подробно и вежливо."
            }
        ]
    return conversation_history[user_id]

def add_user_message(user_id, message):
    history = get_user_history(user_id)
    history.append({
        "role": "user",
        "content": message
    })
    
def add_assistant_message(user_id, message):
    history = get_user_history(user_id)
    history.append({
        "role": "assistant", 
        "content": message
    })

def clear_history(user_id):
    if user_id in conversation_history:
        system_msg = conversation_history[user_id][0]  # сохраняем системный промпт
        conversation_history[user_id] = [system_msg]


# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить историю нашего диалога\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')

@bot.message_handler(commands=['clear'])
def clear_conversation(message):
    user_id = message.from_user.id
    clear_history(user_id)
    bot.reply_to(message, "История диалога очищена!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    add_user_message(user_id, user_query)
    history = get_user_history(user_id)
    request = {
        "messages": history
    }

    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request,
        timeout=60
    )

    if response.status_code == 200:
        model_response :ModelResponse = jsons.loads(response.text, ModelResponse)
        assistant_reply = model_response.choices[0].message.content
        add_assistant_message(user_id, assistant_reply)
        bot.reply_to(message, assistant_reply)
    else:
        history.pop()
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)