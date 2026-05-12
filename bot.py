import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
ContextTypes, MessageHandler, filters, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

CHOOSE_NAME = 0

PEOPLE = {
“ilyas”:  {“name”: “Ильяс”,  “emoji”: “👨”},
“azhar”:  {“name”: “Ажар”,   “emoji”: “👩”},
“karina”: {“name”: “Карина”, “emoji”: “👱‍♀️”},
}

TASKS = {
“kitchen”: {“name”: “Помыл(а) кухню”,      “emoji”: “🍳”, “pts”: 3},
“dishes”:  {“name”: “Помыл(а) посуду”,      “emoji”: “🍽”, “pts”: 2},
“trash”:   {“name”: “Вынес(ла) мусор”,      “emoji”: “🗑”, “pts”: 2},
“shoes”:   {“name”: “Убрал(а) обувь”,       “emoji”: “👟”, “pts”: 1},
“toys”:    {“name”: “Убрал(а) игрушки”,     “emoji”: “🧸”, “pts”: 2, “max_per_day”: 2},
“general”: {“name”: “Генеральная уборка”,   “emoji”: “🧹”, “pts”: 5},
}

DATA_FILE = “scores.json”
GROUP_CHAT_ID = int(os.environ.get(“GROUP_CHAT_ID”, “0”))

# ─── Хранилище ────────────────────────────────────────────────────────────────

def load_data():
if os.path.exists(DATA_FILE):
with open(DATA_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {
“scores”: {“ilyas”: 0, “azhar”: 0, “karina”: 0},
“history”: [],
“today_count”: {},
“users”: {}
}

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, ensure_ascii=False, indent=2)

def get_loser(scores):
return min(scores, key=scores.get)

def get_pid(user_id, data):
return data.get(“users”, {}).get(str(user_id))

def scores_text(scores):
loser_id = get_loser(scores)
lines = []
for i, pid in enumerate(sorted(PEOPLE.keys(), key=lambda p: scores[p], reverse=True)):
p = PEOPLE[pid]
medal = [“🥇”, “🥈”, “🥉”][i]
cinema = “ 🎬” if pid == loser_id else “”
lines.append(f”{medal} {p[‘emoji’]} {p[‘name’]}: {scores[pid]} бал.{cinema}”)
lines.append(f”\n🎬 В кино ведёт: *{PEOPLE[loser_id][‘name’]}*”)
return “\n”.join(lines)

def tasks_keyboard():
keyboard = []
for tid, t in TASKS.items():
keyboard.append([InlineKeyboardButton(
f”{t[‘emoji’]} {t[‘name’]} (+{t[‘pts’]} бал)”,
callback_data=f”done_{tid}”
)])
keyboard.append([InlineKeyboardButton(“🏆 Счёт”, callback_data=“show_scores”)])
keyboard.append([InlineKeyboardButton(“📜 История”, callback_data=“show_history”)])
return InlineKeyboardMarkup(keyboard)

# ─── /start ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# Игнорируем если это группа
if update.effective_chat.type != “private”:
return ConversationHandler.END

```
user_id = str(update.effective_user.id)
data = load_data()

if user_id in data.get("users", {}):
    pid = data["users"][user_id]
    p = PEOPLE[pid]
    await update.message.reply_text(
        f"Привет, {p['emoji']} *{p['name']}*! Выбери задачу:",
        parse_mode="Markdown",
        reply_markup=tasks_keyboard()
    )
    return ConversationHandler.END

keyboard = [[InlineKeyboardButton(f"{p['emoji']} {p['name']}", callback_data=f"reg_{k}")]
            for k, p in PEOPLE.items()]
await update.message.reply_text(
    "👋 Привет! Кто ты?",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
return CHOOSE_NAME
```

async def choose_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
pid = query.data.replace(“reg_”, “”)
user_id = str(query.from_user.id)
data = load_data()
if “users” not in data:
data[“users”] = {}
data[“users”][user_id] = pid
save_data(data)
p = PEOPLE[pid]
await query.message.reply_text(
f”✅ {p[‘emoji’]} *{p[‘name’]}*, ты зарегистрирован(а)!\n\nВыбери задачу:”,
parse_mode=“Markdown”,
reply_markup=tasks_keyboard()
)
return ConversationHandler.END

# ─── Кнопки ───────────────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
data_cb = query.data
user_id = str(query.from_user.id)
data = load_data()

```
if data_cb == "show_scores":
    await query.message.reply_text(
        f"🏆 *Счёт за месяц:*\n\n{scores_text(data['scores'])}",
        parse_mode="Markdown"
    )

elif data_cb == "show_history":
    history = data.get("history", [])
    if not history:
        await query.message.reply_text("📜 История пока пуста.")
        return
    lines = ["📜 *Последние 10 действий:*\n"]
    for entry in reversed(history[-10:]):
        lines.append(f"• {entry}")
    await query.message.reply_text("\n".join(lines), parse_mode="Markdown")

elif data_cb == "show_tasks":
    await query.message.reply_text(
        "📋 Выбери задачу:",
        reply_markup=tasks_keyboard()
    )

elif data_cb.startswith("done_"):
    tid = data_cb.replace("done_", "")
    task = TASKS.get(tid)
    if not task:
        return

    pid = get_pid(user_id, data)
    if not pid:
        await query.message.reply_text("Сначала напиши /start и выбери своё имя.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    max_per_day = task.get("max_per_day", 1)
    count_key = f"{tid}_{user_id}_{today}"
    today_count = data.get("today_count", {})
    done_today = today_count.get(count_key, 0)

    if done_today >= max_per_day:
        limit_msg = f"{max_per_day} раза" if max_per_day == 2 else "1 раз"
        await query.message.reply_text(f"⛔ Эта задача уже выполнена сегодня (максимум {limit_msg}).")
        return

    # Сохраняем ожидание фото
    context.user_data["pending_task"] = tid
    context.user_data["pending_pid"] = pid
    await query.message.reply_text(
        f"📸 Отправь фото — докажи что *{task['name']}* выполнено!",
        parse_mode="Markdown"
    )
```

# ─── Получение фото ───────────────────────────────────────────────────────────

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_chat.type != “private”:
return

```
user_id = str(update.effective_user.id)
tid = context.user_data.get("pending_task")
pid = context.user_data.get("pending_pid")

if not tid or not pid:
    await update.message.reply_text(
        "Сначала выбери задачу 👇",
        reply_markup=tasks_keyboard()
    )
    return

task = TASKS.get(tid)
data = load_data()
today = datetime.now().strftime("%Y-%m-%d")
max_per_day = task.get("max_per_day", 1)
count_key = f"{tid}_{user_id}_{today}"
today_count = data.get("today_count", {})
done_today = today_count.get(count_key, 0)

if done_today >= max_per_day:
    await update.message.reply_text("⛔ Эта задача уже выполнена сегодня.")
    context.user_data.clear()
    return

# Начисляем баллы
data["scores"][pid] += task["pts"]
today_count[count_key] = done_today + 1
data["today_count"] = today_count
p = PEOPLE[pid]
now_str = datetime.now().strftime("%d.%m %H:%M")
entry = f"{task['emoji']} {p['name']} — {task['name']} +{task['pts']} бал ({now_str})"
data["history"].append(entry)
save_data(data)

scores = data["scores"]
loser_id = get_loser(scores)

caption = (
    f"✅ {p['emoji']} *{p['name']}* выполнил(а):\n"
    f"{task['emoji']} {task['name']}\n"
    f"💰 +{task['pts']} бал → итого: *{scores[pid]} бал.*\n\n"
    f"🏆 *Счёт:*\n{scores_text(scores)}"
)

photo = update.message.photo[-1].file_id
keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton("📋 Задачи", callback_data="show_tasks"),
    InlineKeyboardButton("🏆 Счёт", callback_data="show_scores")
]])

# Личный ответ
await update.message.reply_photo(
    photo=photo,
    caption=f"✅ Засчитано! +{task['pts']} бал.",
    reply_markup=keyboard
)

# Публикуем в группу
if GROUP_CHAT_ID:
    await context.bot.send_photo(
        chat_id=GROUP_CHAT_ID,
        photo=photo,
        caption=caption,
        parse_mode="Markdown"
    )

context.user_data.clear()
```

# ─── Еженедельное напоминание ─────────────────────────────────────────────────

async def weekly_reminder(context: ContextTypes.DEFAULT_TYPE):
if not GROUP_CHAT_ID:
return
data = load_data()
scores = data[“scores”]
text = (
f”📅 *Напоминание — не забываем убираться!*\n\n”
f”🏆 Текущий счёт:\n{scores_text(scores)}\n\n”
f”Кто меньше всех убирается — ведёт всех в кино 🎬”
)
await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text, parse_mode=“Markdown”)

# ─── Авто-сброс в начале месяца ──────────────────────────────────────────────

async def monthly_reset(context: ContextTypes.DEFAULT_TYPE):
if not GROUP_CHAT_ID:
return
data = load_data()
scores = data[“scores”]
loser_id = get_loser(scores)
loser = PEOPLE[loser_id]

```
# Объявляем итоги
text = (
    f"🎉 *Месяц закончился! Итоги:*\n\n"
    f"{scores_text(scores)}\n\n"
    f"🎬 {loser['emoji']} *{loser['name']}* ведёт всех в кино!\n\n"
    f"Счёт сброшен. Новый месяц — новые шансы! 💪"
)
await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text, parse_mode="Markdown")

# Сбрасываем
data["scores"] = {"ilyas": 0, "azhar": 0, "karina": 0}
data["history"] = []
data["today_count"] = {}
save_data(data)
```

# ─── Запуск ───────────────────────────────────────────────────────────────────

def main():
token = os.environ.get(“BOT_TOKEN”)
if not token:
raise ValueError(“Нет BOT_TOKEN!”)

```
app = Application.builder().token(token).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={CHOOSE_NAME: [CallbackQueryHandler(choose_name, pattern="^reg_")]},
    fallbacks=[],
)

app.add_handler(conv)
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_received))

# Напоминание каждое воскресенье в 10:00
app.job_queue.run_daily(
    weekly_reminder,
    time=datetime.strptime("10:00", "%H:%M").time(),
    days=(6,)  # 6 = воскресенье
)

# Сброс 1-го числа каждого месяца в 00:01
app.job_queue.run_monthly(
    monthly_reset,
    when=datetime.strptime("00:01", "%H:%M").time(),
    day=1
)

logger.info("Бот запущен!")
app.run_polling(drop_pending_updates=True)
```

if **name** == “**main**”:
main()
