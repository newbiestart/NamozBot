import json
import requests
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup # Although not strictly used, good practice for type hinting

# Bot tokeni environment variable'dan olinadi
TELE_TOKEN = os.environ.get('TELE_TOKEN')
URL = f"https://api.telegram.org/bot{TELE_TOKEN}/"

# Viloyatlar va shaharlar ro'yxati
viloyatlar = {
    "Andijon viloyati": ["Andijon", "Rishton", "Xo'jabod"],
    "Buxoro viloyati": ["Buxoro", "G'ijduvon", "Qorako'l"],
    "Farg'ona viloyati": ["Farg'ona", "Qo'qon", "Marg'ilon"],
    "Jizzax viloyati": ["Jizzax", "Zomin", "G'allaorol"],
    "Namangan viloyati": ["Namangan", "Chust", "Kosonsoy"],
    "Navoiy viloyati": ["Navoiy", "Nurota", "Qiziltepa"],
    "Qashqadaryo viloyati": ["Qarshi", "G'uzor", "Koson"],
    "Samarqand viloyati": ["Samarqand", "Kattaqo'rg'on", "Urgut"],
    "Sirdaryo viloyati": ["Guliston", "Sirdaryo"],
    "Surxondaryo viloyati": ["Termiz", "Denov", "Boysun"],
    "Toshkent viloyati": ["Bekobod", "Angren", "Chirchiq"],
    "Xorazm viloyati": ["Urganch", "Xiva", "Shovot"],
    "Toshkent shahri": ["Toshkent"],
    "Qoraqalpog'iston Respublikasi": ["Nukus", "Mo'ynoq", "Taxtako'pir"]
}

def send_message(chat_id, text, reply_markup=None):
    params = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    requests.get(URL + "sendMessage", params=params)

def answer_callback_query(callback_query_id, text=None):
    params = {'callback_query_id': callback_query_id} # Corrected: Removed standalone 'callback_query'
    if text:
        params['text'] = text
    requests.get(URL + "answerCallbackQuery", params=params)

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    params = {'chat_id': chat_id, 'message_id': message_id, 'text': text} # Corrected: message_id28 to message_id
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    requests.get(URL + "editMessageText", params=params)

def start(update, context):
    chat_id = update['message']['chat_id']
    keyboard = [[InlineKeyboardButton("Namoz vaqtlari", callback_data="namoz_vaqtlari")]]
    reply_markup = {'inline_keyboard': keyboard}
    send_message(chat_id, "Assalomu alaykum! Botimizga xush kelibsiz.", reply_markup)

def button_callback(update, context):
    query = update['callback_query']
    chat_id = query['message']['chat_id']
    message_id = query['message']['message_id']
    query_data = query['data']

    if query_data == "namoz_vaqtlari":
        keyboard = [[InlineKeyboardButton(v, callback_data=v)] for v in viloyatlar.keys()]
        reply_markup = {'inline_keyboard': keyboard}
        edit_message_text(chat_id, message_id, "Viloyatni tanlang:", reply_markup)
    elif query_data in viloyatlar:
        cities = viloyatlar.get(query_data, [])
        if cities:
            keyboard = [[InlineKeyboardButton(c, callback_data=f"city_{c}")] for c in cities]
            reply_markup = {'inline_keyboard': keyboard}
            edit_message_text(chat_id, message_id, f"{query_data} viloyatida shaharni tanlang:", reply_markup)
        else:
            send_message(chat_id, "Bu viloyat uchun shaharlar mavjud emas.")
    elif query_data.startswith("city_"):
        city = query_data.split("_")[1]
        api_url = f"https://islomapi.uz/api/present/day?region={city}"
        
        try:
            response = requests.get(api_url) # Corrected: Added () to call .get()
            response.raise_for_status() # Check for HTTP errors
            prayer_times_data = response.json()

            # Extracting relevant information
            times = prayer_times_data.get('times', {})
            date = prayer_times_data.get('date', 'N/A')
            weekday = prayer_times_data.get('weekday', 'N/A')

            message_text = (
                f"🕋 Namoz vaqtlari ({city}) - {date}, {weekday}\n\n"
                f"🌅 Bomdod: {times.get('tong_saharlik', 'N/A')}\n"
                f"☀️ Quyosh: {times.get('quyosh', 'N/A')}\n"
                f"🕌 Peshin: {times.get('peshin', 'N/A')}\n"
                f"🌆 Asr: {times.get('asr', 'N/A')}\n"
                f"🌙 Shom: {times.get('shom_iftor', 'N/A')}\n"
                f"🌃 Xufton: {times.get('hufton', 'N/A')}"
            )
            send_message(chat_id, message_text)
        except requests.exceptions.RequestException as e:
            send_message(chat_id, f"Namoz vaqtlarini olishda xato yuz berdi: {e}")
        except json.JSONDecodeError:
            send_message(chat_id, "API dan noto'g'ri javob keldi.")
        except Exception as e:
            send_message(chat_id, f"Kutilmagan xato: {e}")


def lambda_handler(event, context):
    try:
        update = json.loads(event['body'])
        if 'message' in update:
            start(update, None)
        elif 'callback_query' in update:
            button_callback(update, None)
        return {'statusCode': 200, 'body': json.dumps('OK')}
    except Exception as e:
        print(e)
        return {'statusCode': 500, 'body': json.dumps('Error')}