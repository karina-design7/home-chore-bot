import os
import json
import logging
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
ContextTypes, MessageHandler, filters, ConversationHandler,
)

logging.basicConfig(format=’%(asctime)s %(levelname)s %(message)s’, level=logging.INFO)
logger = logging.getLogger(**name**)

CHOOSE_NAME = 0
DATA_FILE = ‘scores.json’

E_MAN    = ‘\U0001f468’
E_WOMAN  = ‘\U0001f469’
E_GIRL   = ‘\U0001f471’
E_POT    = ‘\U0001f373’
E_PLATE  = ‘\U0001f37d’
E_BIN    = ‘\U0001f5d1’
E_SHOE   = ‘\U0001f45f’
E_BEAR   = ‘\U0001f9f8’
E_BROOM  = ‘\U0001f9f9’
E_GOLD   = ‘\U0001f947’
E_SILVER = ‘\U0001f948’
E_BRONZE = ‘\U0001f949’
E_CINEMA = ‘\U0001f3ac’
E_CHECK  = ‘\u2705’
E_STOP   = ‘\u26d4’
E_CAM    = ‘\U0001f4f8’
E_BELL   = ‘\U0001f514’
E_PARTY  = ‘\U0001f389’
E_MUSCLE = ‘\U0001f4aa’
E_TROPHY = ‘\U0001f3c6’
E_SCROLL = ‘\U0001f4dc’
E_MONEY  = ‘\U0001f4b0’
E_CLIP   = ‘\U0001f4cb’
E_RESET  = ‘\U0001f504’

PEOPLE = {
‘ilyas’:  {‘name’: ‘Ilyas’,  ‘emoji’: E_MAN},
‘azhar’:  {‘name’: ‘Azhar’,  ‘emoji’: E_WOMAN},
‘karina’: {‘name’: ‘Karina’, ‘emoji’: E_GIRL},
}

TASKS = {
‘kitchen’: {‘name’: ‘Pomyla kukhnyu’,    ‘emoji’: E_POT,   ‘pts’: 3},
‘dishes’:  {‘name’: ‘Pomyla posudu’,     ‘emoji’: E_PLATE, ‘pts’: 2},
‘trash’:   {‘name’: ‘Vynesla musor’,     ‘emoji’: E_BIN,   ‘pts’: 2},
‘shoes’:   {‘name’: ‘Ubrala obuv’,       ‘emoji’: E_SHOE,  ‘pts’: 1},
‘toys’:    {‘name’: ‘Ubrala igrushki’,   ‘emoji’: E_BEAR,  ‘pts’: 2, ‘max_per_day’: 2},
‘general’: {‘name’: ‘Generalnaya uborka’,‘emoji’: E_BROOM, ‘pts’: 5},
}

def load_data():
if os.path.exists(DATA_FILE):
with open(DATA_FILE, ‘r’, encoding=‘utf-8’) as f:
return json.load(f)
return {‘scores’: {‘ilyas’: 0, ‘azhar’: 0, ‘karina’: 0},
‘history’: [], ‘today_count’: {}, ‘users’: {}, ‘pending’: {}}

def save_data(data):
with open(DATA_FILE, ‘w’, encoding=‘utf-8’) as f:
json.dump(data, f, ensure_ascii=False, indent=2)

def get_loser(scores):
return min(scores, key=scores.get)

def get_pid(uid, data):
return data.get(‘users’, {}).get(str(uid))

def scores_text(scores):
lid = get_loser(scores)
medals = [E_GOLD, E_SILVER, E_BRONZE]
lines = []
for i, pid in enumerate(sorted(PEOPLE.keys(), key=lambda p: scores[p], reverse=True)):
p = PEOPLE[pid]
cin = ’ ’ + E_CINEMA if pid == lid else ‘’
lines.append(medals[i] + ’ ’ + p[‘emoji’] + ’ ’ + p[‘name’] + ‘: ’ + str(scores[pid]) + ’ bal.’ + cin)
lines.append(’’)
lines.append(E_CINEMA + ’ V kino vedet: *’ + PEOPLE[lid][‘name’] + ’*’)
return chr(10).join(lines)

def tasks_keyboard():
rows = []
for tid, t in TASKS.items():
lbl = t[‘emoji’] + ’ ’ + t[‘name’] + ’ (+’ + str(t[‘pts’]) + ’ bal)’
rows.append([InlineKeyboardButton(lbl, callback_data=‘done_’ + tid)])
rows.append([InlineKeyboardButton(E_TROPHY + ’ Schet’, callback_data=‘show_scores’),
InlineKeyboardButton(E_SCROLL + ’ Istoriya’, callback_data=‘show_history’)])
return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = str(update.effective_user.id)
data = load_data()
if uid in data.get(‘users’, {}):
pid = data[‘users’][uid]
p = PEOPLE[pid]
await update.message.reply_text(p[‘emoji’] + ’ *’ + p[‘name’] + ’*, vyberi zadachu:’,
parse_mode=‘Markdown’, reply_markup=tasks_keyboard())
return ConversationHandler.END
kb = [[InlineKeyboardButton(p[‘emoji’] + ’ ’ + p[‘name’], callback_data=‘reg_’ + k)]
for k, p in PEOPLE.items()]
await update.message.reply_text(‘Privet! Kto ty?’, reply_markup=InlineKeyboardMarkup(kb))
return CHOOSE_NAME

async def choose_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()
pid = q.data.replace(‘reg_’, ‘’)
uid = str(q.from_user.id)
data = load_data()
data.setdefault(‘users’, {})[uid] = pid
save_data(data)
p = PEOPLE[pid]
msg = E_CHECK + ’ ’ + p[‘emoji’] + ’ *’ + p[‘name’] + ’*, zaregistrirovan!’ + chr(10) + chr(10) + ‘Vyberi zadachu:’
await q.message.reply_text(msg, parse_mode=‘Markdown’, reply_markup=tasks_keyboard())
return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()
cb = q.data
uid = str(q.from_user.id)
data = load_data()
if cb == ‘show_scores’:
await q.message.reply_text(E_TROPHY + ’ *Schet za mesyac:*’ + chr(10) + chr(10) + scores_text(data[‘scores’]), parse_mode=‘Markdown’)
elif cb == ‘show_history’:
hist = data.get(‘history’, [])
if not hist:
await q.message.reply_text(‘Istoriya poka pusta.’)
return
lines = [E_SCROLL + ’ *Poslednie 10:*’ + chr(10)]
for e in reversed(hist[-10:]):
lines.append(’- ’ + e)
await q.message.reply_text(chr(10).join(lines), parse_mode=‘Markdown’)
elif cb == ‘show_tasks’:
await q.message.reply_text(‘Vyberi zadachu:’, reply_markup=tasks_keyboard())
elif cb.startswith(‘done_’):
tid = cb[5:]
task = TASKS.get(tid)
if not task:
return
pid = get_pid(uid, data)
if not pid:
await q.message.reply_text(‘Snachala napishi /start i vyberi imya.’)
return
today = datetime.now().strftime(’%Y-%m-%d’)
mpd = task.get(‘max_per_day’, 1)
ck = tid + ‘*’ + uid + ’*’ + today
done = data.get(‘today_count’, {}).get(ck, 0)
if done >= mpd:
await q.message.reply_text(E_STOP + ’ Uzhe vypolneno segodnya (max ’ + str(mpd) + ‘x).’)
return
data.setdefault(‘pending’, {})[uid] = tid
save_data(data)
p = PEOPLE[pid]
msg = E_CAM + ’ ’ + p[‘emoji’] + ’ *’ + p[‘name’] + ’*, otprav foto - dokazhi chto *’ + task[‘name’] + ’* vypolneno!’
await q.message.reply_text(msg, parse_mode=‘Markdown’)

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = str(update.effective_user.id)
data = load_data()
tid = data.get(‘pending’, {}).get(uid)
if not tid:
return
pid = get_pid(uid, data)
if not pid:
return
task = TASKS[tid]
today = datetime.now().strftime(’%Y-%m-%d’)
mpd = task.get(‘max_per_day’, 1)
ck = tid + ‘*’ + uid + ’*’ + today
tc = data.get(‘today_count’, {})
done = tc.get(ck, 0)
if done >= mpd:
await update.message.reply_text(E_STOP + ’ Eta zadacha uzhe vypolnena segodnya.’)
data[‘pending’].pop(uid, None)
save_data(data)
return
data[‘scores’][pid] += task[‘pts’]
tc[ck] = done + 1
data[‘today_count’] = tc
data[‘pending’].pop(uid, None)
p = PEOPLE[pid]
now_str = datetime.now().strftime(’%d.%m %H:%M’)
entry = task[‘emoji’] + ’ ’ + p[‘name’] + ’ - ’ + task[‘name’] + ’ +’ + str(task[‘pts’]) + ’ bal (’ + now_str + ‘)’
data[‘history’].append(entry)
save_data(data)
sc = data[‘scores’]
nl = chr(10)
cap = (E_CHECK + ’ ’ + p[‘emoji’] + ’ *’ + p[‘name’] + ’* vypolnil(a):’ + nl
+ task[‘emoji’] + ’ ’ + task[‘name’] + nl
+ E_MONEY + ’ +’ + str(task[‘pts’]) + ’ bal - itogo: *’ + str(sc[pid]) + ’ bal.*’ + nl + nl
+ E_TROPHY + ’ *Schet:*’ + nl + scores_text(sc))
photo = update.message.photo[-1].file_id
kb = InlineKeyboardMarkup([[InlineKeyboardButton(E_CLIP + ’ Zadachi’, callback_data=‘show_tasks’),
InlineKeyboardButton(E_TROPHY + ’ Schet’, callback_data=‘show_scores’)]])
await update.message.reply_photo(photo=photo, caption=cap, parse_mode=‘Markdown’, reply_markup=kb)

async def weekly_reminder(context: ContextTypes.DEFAULT_TYPE):
data = load_data()
nl = chr(10)
text = E_BELL + ’ *Ne zabyvaem ubiratsya!*’ + nl + nl + E_TROPHY + ’ Schet:’ + nl + scores_text(data[‘scores’]) + nl + nl + ’Kto menshe - vedet v kino ’ + E_CINEMA
await context.bot.send_message(chat_id=context.job.chat_id, text=text, parse_mode=‘Markdown’)

async def monthly_reset(context: ContextTypes.DEFAULT_TYPE):
data = load_data()
sc = data[‘scores’]
lid = get_loser(sc)
loser = PEOPLE[lid]
nl = chr(10)
text = (E_PARTY + ’ *Mesyac zakonchilsya!*’ + nl + nl + scores_text(sc) + nl + nl
+ E_CINEMA + ’ ’ + loser[‘emoji’] + ’ *’ + loser[‘name’] + ’* vedet vsekh v kino!’ + nl + nl
+ ’Schet sbrosen. Novyy mesyac ’ + E_MUSCLE)
await context.bot.send_message(chat_id=context.job.chat_id, text=text, parse_mode=‘Markdown’)
data[‘scores’] = {‘ilyas’: 0, ‘azhar’: 0, ‘karina’: 0}
data[‘history’] = []
data[‘today_count’] = {}
save_data(data)

async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
cid = update.effective_chat.id
jq = context.job_queue
for job in jq.get_jobs_by_name(‘weekly’) + jq.get_jobs_by_name(‘monthly’):
job.schedule_removal()
jq.run_daily(weekly_reminder, time=time(10, 0), days=(6,), chat_id=cid, name=‘weekly’)
jq.run_monthly(monthly_reset, when=time(0, 1), day=1, chat_id=cid, name=‘monthly’)
nl = chr(10)
await update.message.reply_text(E_CHECK + ’ Gotovo!’ + nl + E_BELL + ’ Napominanie kazhdoe voskresenye v 10:00’ + nl + E_RESET + ’ Sbros 1-go chisla’)

def main():
token = os.environ.get(‘BOT_TOKEN’)
if not token:
raise RuntimeError(‘BOT_TOKEN not set’)
app = Application.builder().token(token).build()
conv = ConversationHandler(
entry_points=[CommandHandler(‘start’, start)],
states={CHOOSE_NAME: [CallbackQueryHandler(choose_name, pattern=’^reg_’)]},
fallbacks=[],
)
app.add_handler(conv)
app.add_handler(CommandHandler(‘setup’, setup))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.PHOTO, photo_received))
logger.info(‘Bot started’)
app.run_polling(drop_pending_updates=True)

if **name** == ‘**main**’:
main()
