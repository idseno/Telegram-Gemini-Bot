import telebot
import google.generativeai as genai
import time
import json
import os
from telebot import types

# ---------------------------------------------------------
# 1. إعدادات البوت والمفاتيح (املأها هنا)
# ---------------------------------------------------------

TELEGRAM_BOT_TOKEN = "7231863128:AAFA6WMZZmHmpAl_dW6sBXqrPnkJhaEEtSc"

API_KEYS = [
    "AIzaSyB4NMbPldqHfiRnwGPGx1RScMdMbDRE6ac",
    "AIzaSyAr4agg8dYLNkgIRKEU8G8618g23B3v2rQ",
    "AIzaSyCMy66e3QLgT93a4YkUMtFhfwtezaczIOc"
]

ADMIN_ID = 641799099  # رقم الآيدي الخاص بك

# ---------------------------------------------------------
# 2. إعدادات النظام (لا تغير شيئاً هنا)
# ---------------------------------------------------------

DB_FILE = "bot_data.json"
current_key_index = 0

# إعدادات إلغاء الفلاتر للسماح بجميع الأسئلة
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# بيانات افتراضية
default_data = {
    "channel_user": "@owoooooo",
    "start_message": "أهلاً بك! 🤖\nأرسل سؤالك مباشرة.",
    "users": []
}

# دوال الذاكرة
def load_data():
    if not os.path.exists(DB_FILE):
        save_data(default_data)
        return default_data
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default_data

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

bot_data = load_data()

# دوال الذكاء الاصطناعي
def configure_genai():
    global current_key_index
    try:
        genai.configure(api_key=API_KEYS[current_key_index])
        # استخدام الاسم الذي يعمل في حسابك
        return genai.GenerativeModel('models/gemini-flash-latest', safety_settings=safety_settings)
    except Exception as e:
        print(f"Error configuring key: {e}")
        return None

def switch_api_key():
    global current_key_index, model, chat_session
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"🔄 Switching to Key #{current_key_index + 1}")
    model = configure_genai()
    chat_session = model.start_chat(history=[])

# تشغيل البوت
model = configure_genai()
chat_session = model.start_chat(history=[])
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# دالة التحقق من الاشتراك
def check_subscription(user_id):
    channel = bot_data['channel_user']
    if channel == "@YourChannel": return True
    try:
        member = bot.get_chat_member(channel, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return True

# دالة بناء الأزرار الرئيسية
def build_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # يجب أن تعدل هذه المعلومات (ضع معرفك وأسماء الأزرار التي تريدها)
    btn1 = types.InlineKeyboardButton("🔑 الاشتراك المدفوع", callback_data='paid_sub')
    btn2 = types.InlineKeyboardButton("⚙️ إعدادات المطور", callback_data='dev_settings')
    btn3 = types.InlineKeyboardButton("💬 التواصل والإبلاغ", url='https://t.me/idseno') 
    btn4 = types.InlineKeyboardButton("💡 التعليمات", callback_data='help_info')
    
    markup.add(btn1, btn2, btn3, btn4)
    return markup
    
# ---------------------------------------------------------
# 3. الأوامر ووظائف البوت
# ---------------------------------------------------------

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id == ADMIN_ID:
        users_count = len(bot_data['users'])
        bot.reply_to(message, f"📊 Users: {users_count}\n📢 Channel: {bot_data['channel_user']}")

@bot.message_handler(commands=['setchannel'])
def set_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            bot_data['channel_user'] = message.text.split()[1]
            save_data(bot_data)
            bot.reply_to(message, "✅ Channel Updated.")
        except:
            bot.reply_to(message, "Error. Use: /setchannel @user")

@bot.message_handler(commands=['setstart'])
def set_start(message):
    if message.from_user.id == ADMIN_ID:
        try:
            bot_data['start_message'] = message.text.split(maxsplit=1)[1]
            save_data(bot_data)
            bot.reply_to(message, "✅ Start Message Updated.")
        except:
            bot.reply_to(message, "Error. Use: /setstart Text")

@bot.message_handler(commands=['start', 'new'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in bot_data['users']:
        bot_data['users'].append(user_id)
        save_data(bot_data)
    
    global chat_session
    chat_session = model.start_chat(history=[])
    
    # إرسال رسالة الترحيب مع الأزرار
    bot.reply_to(message, bot_data['start_message'], reply_markup=build_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        channel = bot_data['channel_user']
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(text="اشترك هنا ✅", url=f"https://t.me/{channel.replace('@','')}")
        markup.add(btn)
        bot.reply_to(message, f"⚠️ يجب الاشتراك في {channel} أولاً.", reply_markup=markup)
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        response = chat_session.send_message(message.text)
        
        if len(response.text) > 4000:
            for i in range(0, len(response.text), 4000):
                bot.reply_to(message, response.text[i:i+4000])
        else:
            bot.reply_to(message, response.text)

    except Exception as e:
        err = str(e)
        print(f"❌ Error: {err}")
        if "429" in err or "Quota" in err:
            switch_api_key()
            bot.reply_to(message, "جاري التبديل للمفتاح التالي... 🔄 أعد إرسال رسالتك.")
        else:
            bot.reply_to(message, "حدث خطأ بسيط، حاول مرة أخرى.")
            
# دالة معالجة ضغطات الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    
    if call.data == 'paid_sub':
        bot.send_message(call.message.chat.id, "للاشتراك المدفوع، تواصل مع المطور: @idseno") # عدل معرفك هنا
        
    elif call.data == 'dev_settings':
        if call.from_user.id == ADMIN_ID:
            bot.send_message(call.message.chat.id, "أهلاً أيها المدير!\nالأوامر السرية هي:\n/stats\n/setchannel\n/setstart")
        else:
            bot.send_message(call.message.chat.id, "هذه القائمة خاصة بالمطورين فقط.")
            
    elif call.data == 'help_info':
        bot.send_message(call.message.chat.id, "يمكنك الآن طرح أسئلتك مباشرة. البوت يتذكر المحادثة السابقة.")
    
    bot.answer_callback_query(call.id) # إيقاف "انتظار التحميل" من الزر

print("✅ Bot Started Successfully (Final Version)")
bot.infinity_polling()