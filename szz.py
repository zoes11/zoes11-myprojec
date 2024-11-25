import telebot
from telebot import types
import requests
import json
from telebot.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mak

token = ""
bot = telebot.TeleBot(token)

def load_data():
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {"users": [], "required_channels": [], "admin_ids": [1471911848], "subscription_message": "🚫 يجب عليك الاشتراك في القنوات/المجموعات المطلوبة أولاً."}

def save_data():
    with open("data.json", "w") as f:
        json.dump({
            "users": list(users),
            "required_channels": required_channels,
            "admin_ids": list(admin_ids),
            "subscription_message": subscription_message
        }, f)

data = load_data()
users = set(data["users"])
required_channels = data["required_channels"]
admin_ids = set(data["admin_ids"])
subscription_message = data["subscription_message"]

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id in admin_ids:
        markup = Mak()
        markup.add(Btn("📢 إذاعة", callback_data="broadcast"))
        markup.add(Btn("👥 عرض المستخدمين", callback_data="show_users"))  
        markup.add(Btn("🔗 إضافة اشتراك إجباري", callback_data="add_subscription"))
        markup.add(Btn("📝 إضافة كليشة اشتراك", callback_data="set_subscription_message"))
        markup.add(Btn("➕ إضافة أدمن", callback_data="add_admin"))
        markup.add(Btn("❌ حذف اشتراك إجباري", callback_data="remove_subscription"))
        markup.add(Btn("📋 عرض القنوات المطلوبة", callback_data="show_required_channels"))  
        bot.send_message(message.chat.id, "لوحة التحكم", reply_markup=markup)
    else:
        bot.reply_to(message, "🚫 لا تملك صلاحية الوصول إلى لوحة التحكم")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 ارسل الرسالة التي تريد إذاعتها:")
        bot.register_next_step_handler(msg, broadcast_message)
    elif call.data == "show_users":
        show_all_users(call.message)
    elif call.data == "add_subscription":
        msg = bot.send_message(call.message.chat.id, "🔗 ارسل معرف القناة أو المجموعة المطلوبة (بدون @):")
        bot.register_next_step_handler(msg, add_subscription_channel)
    elif call.data == "set_subscription_message":
        msg = bot.send_message(call.message.chat.id, "📝 ارسل الكليشة التي تريدها للاشتراك الإجباري:")
        bot.register_next_step_handler(msg, set_subscription_message)
    elif call.data == "add_admin":
        msg = bot.send_message(call.message.chat.id, "➕ ارسل معرف الأدمن الجديد:")
        bot.register_next_step_handler(msg, add_admin)
    elif call.data == "remove_subscription":
        msg = bot.send_message(call.message.chat.id, "❌ ارسل معرف القناة التي تريد حذفها من الاشتراك الإجباري (بدون @):")
        bot.register_next_step_handler(msg, remove_subscription_channel)
    elif call.data == "show_required_channels":  
        show_required_channels(call.message)

def set_subscription_message(message):
    global subscription_message
    subscription_message = message.text
    save_data()
    bot.send_message(message.chat.id, "✅ تم تعيين كليشة الاشتراك الإجباري بنجاح.")

def add_admin(message):
    try:
        new_admin_id = int(message.text)
        admin_ids.add(new_admin_id)
        save_data()
        bot.send_message(message.chat.id, f"✅ تم إضافة الأدمن بمعرف {new_admin_id} بنجاح.")
    except ValueError:
        bot.send_message(message.chat.id, "🚫 المعرف غير صالح. يرجى إرسال رقم صحيح.")

def show_all_users(message):
    if not users:
        bot.send_message(message.chat.id, "🚫 لا يوجد مستخدمون حاليًا.")
    else:
        user_list = "\n".join([f"• {user_id} - @{bot.get_chat(user_id).username}" for user_id in users])
        bot.send_message(message.chat.id, f"📋 قائمة المستخدمين:\n{user_list}")

def broadcast_message(message):
    for user_id in users:
        try:
            bot.send_message(user_id, message.text)
        except:
            pass

def add_subscription_channel(message):
    global required_channels
    required_channels.append(message.text)
    save_data()
    bot.send_message(message.chat.id, f"🔗 تم إضافة القناة/المجموعة المطلوبة: @{message.text}")

def remove_subscription_channel(message):
    global required_channels
    if message.text in required_channels:
        required_channels.remove(message.text)
        save_data()
        bot.send_message(message.chat.id, f"❌ تم حذف القناة: @{message.text} من الاشتراك الإجباري.")
    else:
        bot.send_message(message.chat.id, "🚫 القناة غير موجودة في قائمة الاشتراك الإجباري.")

def show_required_channels(message):
    if not required_channels:
        bot.send_message(message.chat.id, "🚫 لا توجد قنوات للاشتراك الإجباري حاليًا.")
    else:
        channels_list = "\n".join([f"@{channel}" for channel in required_channels])
        bot.send_message(message.chat.id, f"📋 القنوات المطلوبة للاشتراك:\n{channels_list}")

def is_subscribed(user_id):
    for channel in required_channels:
        try:
            member = bot.get_chat_member(f"@{channel}", user_id)
            if member.status == "left":
                return False
        except:
            return False
    return True

@bot.message_handler(commands=["start"])
def start(message):
    if not is_subscribed(message.from_user.id):
        markup = Mak()
        for channel in required_channels:
            markup.add(Btn(f"اشترك في @{channel}", url=f"https://t.me/{channel}"))
        bot.send_message(message.chat.id, subscription_message, reply_markup=markup)
        return
    
    users.add(message.from_user.id)
    save_data()
    markup = Mak()
    markup.add(Btn("مطور البوت 👨‍🔧", url='https://t.me/z_e_sl'))
    markup.add(Btn("قناتي", url='https://t.me/a_6_7_1'))
    name = message.from_user.first_name
    bot.reply_to(message, f"<b>مرحباً {name}\n-! في بـوت تحميل من تيكـتوك ارسـل الان رابـط لتحميل من فضلك .</b>", parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda brok: True)
def Url(message):
    if not is_subscribed(message.from_user.id):
        markup = Mak()
        for channel in required_channels:
            markup.add(Btn(f"اشترك في @{a_6_7_1}", url=f"https://t.me/{a_6_7_1}"))
        bot.send_message(message.chat.id, subscription_message, reply_markup=markup)
        return

    markup = Mak()
    download_button = Btn("تحميل الفيديو بدقة عالية", url=message.text) 
    markup.add(download_button)

    try:
        msgg = bot.send_message(message.chat.id, "*جاري التحميل ...*", parse_mode="markdown")
        msg = message.text
        url = requests.get(f'https://tikwm.com/api/?url={msg}').json()
        music = url['data']['music']
        region = url['data']['region']
        tit = url['data']['title']
        vid = url['data']['play']
        ava = url['data']['author']['avatar']
        name = url['data']['music_info']['author']
        time = url['data']['duration']
        sh = url['data']['share_count']
        com = url['data']['comment_count']
        wat = url['data']['play_count']
        bot.delete_message(chat_id=message.chat.id, message_id=msgg.message_id)
        bot.send_photo(message.chat.id, ava, caption=f'- اسم الحساب : *{name}*\n - دوله الحساب : *{region}*\n\n- عدد مرات المشاهدة : *{wat}*\n- عدد التعليقات : *{com}*\n- عدد مرات المشاركة : *{sh}*\n- طول الفيديو : *{time}*', parse_mode="markdown")
        bot.send_video(message.chat.id, vid, caption=f"{tit}", reply_markup=markup)

        bot_username = bot.get_me().username
        bot.send_audio(message.chat.id, music, title=f"الموسيقى من الفيديو - @{bot_username}")
    except:
        bot.delete_message(chat_id=message.chat.id, message_id=msgg.message_id)
        bot.reply_to(message, 'حدث خطأ أثناء التحميل.')

print('البوت يعمل...')
bot.infinity_polling()