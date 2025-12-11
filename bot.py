import telebot
import google.generativeai as genai
import time
import json
import os
from telebot import types

# ---------------------------------------------------------
# 1. إعدادات البوت والمفاتيح (يتم قراءتها من Railway/Environment Variables)
# ---------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.environ.get("7231863128:AAFA6WMZZmHmpAl_dW6sBXqrPnkJhaEEtSc")

API_KEYS = [
    os.environ.get("AIzaSyB4NMbPldqHfiRnwGPGx1RScMdMbDRE6ac"),
    os.environ.get("AIzaSyAr4agg8dYLNkgIRKEU8G8618g23B3v2rQ"),
    os.environ.get("AIzaSyCMy66e3QLgT93a4YkUMtFhfwtezaczIOc")
]

# تم إضافة try/except لحل مشكلة 'NoneType' التي ظهرت في السجلات
try:
    ADMIN_ID = int(os.environ.get("ADMIN_ID"))
except:
    ADMIN_ID = 641799099

# ---------------------------------------------------------
# 2. إعدادات النظام
# ---------------------------------------------------------

DB_FILE = "bot_data.json"
current_key_index = 0

# إعدادات إلغاء الفلاتر
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
def configure_genai(model_name):
    global current_key_index
    try:
        if not API_KEYS[current_key_index]:
            return None 

        genai.configure(api_key=API_KEYS[current_key_index])
        return genai.GenerativeModel(model_name, safety_settings=safety_settings)
    except Exception as e:
        print(f"Error configuring key: {e}")
        return None

def switch_api_key():
    global current_key_index, model_text, model_vision, chat_session
    
    for _ in range(len(API_KEYS)):
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        print(f"🔄 Switching to Key #{current_key_index + 1}")
        
        model_text = configure_genai('models/gemini-2.5-flash')
        model_vision = configure_genai('models/gemini-2.5-flash-image')
        
        if model_text:
            chat_session = model_text.start_chat(history=[])
            return True
        
    print("❌ All API keys failed or are missing.")
    return False

# تشغيل البوت
model_text = configure_genai('models/gemini-2.5-flash') 
model_vision = configure_genai('models/gemini-2.5-flash-image')

if not model_text and not switch_api_key():
    print("FATAL ERROR: Bot cannot start without a working Gemini API key.")
    exit() 

chat_session = model_text.start_chat(history=[])
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

# دالة تحميل الصورة من تليجرام
def get_image_path(message):
    try:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = f"temp_image_{message.chat.id}.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        return image_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

# دالة بناء الأزرار الرئيسية
def build_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
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
    chat_session = model_text.start_chat(history=[])
    
    bot.reply_to(message, bot_data['start_message'], reply_markup=build_main_keyboard())

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
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
        
        # --- 1. Vision Logic (Image + Caption) ---
        if message.photo and message.caption:
            user_prompt = message.caption
            image_path = get_image_path(message)
            
            if image_path:
                img = genai.types.contents.Part.from_file(image_path) 
                
                response = model_vision.generate_content([user_prompt, img])
                
                os.remove(image_path)
                
                bot.reply_to(message, response.text)
                return
        
        # --- 2. Standard Chat Logic (Text Only) ---
        elif message.text:
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
            if switch_api_key():
                 bot.reply_to(message, "جاري التبديل للمفتاح التالي... 🔄 أعد إرسال رسالتك.")
            else:
                 bot.reply_to(message, "❌ نفد الرصيد اليومي لجميع المفاتيح. يرجى المحاولة غداً.")
        else:
            bot.reply_to(message, "حدث خطأ بسيط، حاول مرة أخرى.")
            
# دالة معالجة ضغطات الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    
    if call.data == 'paid_sub':
        bot.send_message(call.message.chat.id, "للاشتراك المدفوع، تواصل مع المطور: @idseno")
        
    elif call.data == 'dev_settings':
        if call.from_user.id == ADMIN_ID:
            bot.send_message(call.message.chat.id, "أهلاً أيها المدير!\nالأوامر السرية هي:\n/stats\n/setchannel\n/setstart")
        else:
            bot.send_message(call.message.chat.id, "هذه القائمة خاصة بالمطورين فقط.")
            
    elif call.data == 'help_info':
        bot.send_message(call.message.chat.id, "يمكنك الآن طرح أسئلتك مباشرة. البوت يتذكر المحادثة السابقة.")
    
    bot.answer_callback_query(call.id)

print("✅ Bot Started Successfully (Final Pro Version for Railway)")
bot.infinity_polling()
