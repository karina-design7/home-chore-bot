import os
import json
import logging
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
CommandHandler,
CallbackQueryHandler,
ContextTypes,
MessageHandler,
filters,
ConversationHandler,
)

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO
)
logger = logging.getLogger(**name**)

CHOOSE_NAME = 0
DATA_FILE = “scores.json”

PEOPLE = {
“ilyas”:  {“name”: “Ilyas”,  “emoji”: “\U0001f468”},
“azhar”:  {“name”: “Azhar”,  “emoji”: “\U0001f469”},
“karina”: {“name”: “Karina”, “emoji”: “\U0001f471”},
}

TASKS = {
“kitchen”: {“name”: “Pomyl kukhnyu”,      “emoji”: “\U0001f373”, “pts”: 3},
“dishes”:  {“name”: “Pomyl posudu”,        “emoji”: “\U0001f37d”, “pts”: 2},
“trash”:   {“name”: “Vynes musor”,         “emoji”: “\U0001f5d1”, “pts”: 2},
“shoes”:   {“name”: “Ubral obuv”,          “emoji”: “\U0001f45f”, “pts”: 1},
“toys”:    {“name”: “Ubral igrushki”,      “emoji”: “\U0001f9f8”, “pts”: 2, “max_per_day”: 2},
“general”: {“name”: “Generalnaya uborka”,  “emoji”: “\U0001f9f9”, “pts”: 5},
}

def load_data():
if os.path.exists(DATA_FILE):
with open(DATA_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {
“scores”: {“ilyas”: 0, “azhar”: 0, “karina”: 0},
“history”: [],
“today_count”: {},
“users”: {},
“pending”: {},
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
medals = [”\U0001f947”, “\U0001f948”, “\U0001f949”]
lines = []
for i, pid in enumerate(sorted(PEOPLE.keys(), key=lambda p: scores[p], reverse=True)):
p = PEOPLE[pid]
cinema = “ \U0001f3ac” if pid == loser_id else “”
line = medals[i] + “ “ + p[“emoji”] + “ “ + p[“name”] + “: “ + str(scores[pid]) + “ bal.” + cinema
lines.append(line)
lines.append(”\n\U0001f3ac V kino vedet: *” + PEOPLE[loser_id][“name”] + “*”)
return “\n”.join(lines)

def tasks_keyboard():
keyboard = []
for tid, t in TASKS.items():
label = t[“emoji”] + “ “ + t[“name”] + “ (+” + str(t[“pts”]) + “ bal)”
keyboard.append([InlineKeyboardButton(label, callback_data=“done_” + tid)])
keyboard.append([
InlineKeyboardButton(”\U0001f3c6 Schet”, callback_data=“show_scores”),
InlineKeyboardButton(”\U0001f4dc Istoriya”, callback_data=“show_history”),
])
return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
data = load_data()
if user_id in data.get(“users”, {}):
pid = data[“users”][user_id]
p = PEOPLE[pid]
await update.message.reply_text(
p[“emoji”] + “ *” + p[“name”] + “*, vyberi zadachu:”,
parse_mode=“Markdown”,
reply_markup=tasks_keyboard(),
)
return ConversationHandler.END
keyboard = [
[InlineKeyboardButton(p[“emoji”] + “ “ + p[“name”], callback_data=“reg_” + k)]
for k, p in PEOPLE.items()
]
await update.message.reply_text(“Privet! Kto ty?”, reply_markup=InlineKeyboardMarkup(keyboard))
return CHOOSE_NAME

async def choose_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
pid = query.data.replace(“reg_”, “”)
user_id = str(query.from_user.id)
data = load_data()
data.setdefault(“users”, {})[user_id] = pid
save_data(data)
p = PEOPLE[pid]
await query.message.reply_text(
“\U00002705 “ + p[“emoji”] + “ *” + p[“name”] + “*, zaregistrirovan!\n\nVyberi zadachu:”,
parse_mode=“Markdown”,
reply_markup=tasks_keyboard(),
)
return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
cb = query.data
user_id = str(query.from_user.id)
data = load_data()

```
if cb == "show_scores":
    await query.message.reply_text(
        "\U0001f3c6 *Schet za mesyac:*\n\n" + scores_text(data["scores"]),
        parse_mode="Markdown",
    )

elif cb == "show_history":
    history = data.get("history", [])
    if not history:
        await query.message.reply_text("Historia poka pusta.")
        return
    lines = ["\U0001f4dc *Poslednie 10:*\n"]
    for entry in reversed(history[-10:]):
        lines.append("- " + entry)
    await query.message.reply_text("\n".join(lines), parse_mode="Markdown")

elif cb == "show_tasks":
    await query.message.reply_text("Vyberi zadachu:", reply_markup=tasks_keyboard())

elif cb.startswith("done_"):
    tid = cb[5:]
    task = TASKS.get(tid)
    if not task:
        return
    pid = get_pid(user_id, data)
    if not pid:
        await query.message.reply_text("Snachala napishi /start i vyberi imya.")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    max_per_day = task.get("max_per_day", 1)
    count_key = tid + "_" + user_id + "_" + today
    done_today = data.get("today_count", {}).get(count_key, 0)
    if done_today >= max_per_day:
        await query.message.reply_text(
            "\U000026d4 Uzhe vypolneno segodnya (max " + str(max_per_day) + "x)."
        )
        return
    data.setdefault("pending", {})[user_id] = tid
    save_data(data)
    p = PEOPLE[pid]
    await query.message.reply_text(
        "\U0001f4f8 " + p["emoji"] + " *" + p["name"]
        + "*, otprav foto — dokazhi chto *" + task["name"] + "* vypolneno!",
        parse_mode="Markdown",
    )
```

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
data = load_data()
tid = data.get(“pending”, {}).get(user_id)
if not tid:
return
pid = get_pid(user_id, data)
if not pid:
return
task = TASKS[tid]
today = datetime.now().strftime(”%Y-%m-%d”)
max_per_day = task.get(“max_per_day”, 1)
count_key = tid + “*” + user_id + “*” + today
today_count = data.get(“today_count”, {})
done_today = today_count.get(count_key, 0)
if done_today >= max_per_day:
await update.message.reply_text(”\U000026d4 Eta zadacha uzhe vypolnena segodnya.”)
data[“pending”].pop(user_id, None)
save_data(data)
return
data[“scores”][pid] += task[“pts”]
today_count[count_key] = done_today + 1
data[“today_count”] = today_count
data[“pending”].pop(user_id, None)
p = PEOPLE[pid]
now_str = datetime.now().strftime(”%d.%m %H:%M”)
entry = task[“emoji”] + “ “ + p[“name”] + “ — “ + task[“name”] + “ +” + str(task[“pts”]) + “ bal (” + now_str + “)”
data[“history”].append(entry)
save_data(data)
scores = data[“scores”]
caption = (
“\U00002705 “ + p[“emoji”] + “ *” + p[“name”] + “* vypolnil(a):\n”
+ task[“emoji”] + “ “ + task[“name”] + “\n”
+ “\U0001f4b0 +” + str(task[“pts”]) + “ bal — itogo: *” + str(scores[pid]) + “ bal.*\n\n”
+ “\U0001f3c6 *Schet:*\n” + scores_text(scores)
)
photo = update.message.photo[-1].file_id
keyboard = InlineKeyboardMarkup([[
InlineKeyboardButton(”\U0001f4cb Zadachi”, callback_data=“show_tasks”),
InlineKeyboardButton(”\U0001f3c6 Schet”, callback_data=“show_scores”),
]])
await update.message.reply_photo(
photo=photo, caption=caption, parse_mode=“Markdown”, reply_markup=keyboard
)

async def weekly_reminder(context: ContextTypes.DEFAULT_TYPE):
data = load_data()
text = (
“\U0001f514 *Ne zabyvaem ubiratsya!*\n\n”
+ “\U0001f3c6 Tekushchiy schet:\n”
+ scores_text(data[“scores”])
+ “\n\nKto menshe — vedet v kino \U0001f3ac”
)
await context.bot.send_message(chat_id=context.job.chat_id, text=text, parse_mode=“Markdown”)

async def monthly_reset(context: ContextTypes.DEFAULT_TYPE):
data = load_data()
scores = data[“scores”]
loser_id = get_loser(scores)
loser = PEOPLE[loser_id]
text = (
“\U0001f389 *Mesyac zakonchilsya!*\n\n”
+ scores_text(scores) + “\n\n”
+ “\U0001f3ac “ + loser[“emoji”] + “ *” + loser[“name”] + “* vedet vsekh v kino!\n\n”
+ “Schet sbrosen. Novyy mesyac \U0001f4aa”
)
await context.bot.send_message(chat_id=context.job.chat_id, text=text, parse_mode=“Markdown”)
data[“scores”] = {“ilyas”: 0, “azhar”: 0, “karina”: 0}
data[“history”] = []
data[“today_count”] = {}
save_data(data)

async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
chat_id = update.effective_chat.id
jq = context.job_queue
for job in jq.get_jobs_by_name(“weekly”) + jq.get_jobs_by_name(“monthly”):
job.schedule_removal()
jq.run_daily(weekly_reminder, time=time(10, 0), days=(6,), chat_id=chat_id, name=“weekly”)
jq.run_monthly(monthly_reset, when=time(0, 1), day=1, chat_id=chat_id, name=“monthly”)
await update.message.reply_text(
“\U00002705 Gotovo!\n”
“\U0001f514 Napominanie kazhdoe voskresenye v 10:00\n”
“\U0001f504 Sbros scheta 1-go chisla”
)

def main():
token = os.environ.get(“BOT_TOKEN”)
if not token:
raise RuntimeError(“BOT_TOKEN not set”)
app = Application.builder().token(token).build()
conv = ConversationHandler(
entry_points=[CommandHandler(“start”, start)],
states={CHOOSE_NAME: [CallbackQueryHandler(choose_name, pattern=”^reg_”)]},
fallbacks=[],
)
app.add_handler(conv)
app.add_handler(CommandHandler(“setup”, setup))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.PHOTO, photo_received))
logger.info(“Bot started”)
app.run_polling(drop_pending_updates=True)

if **name** == “**main**”:
main()
