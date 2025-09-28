# chiffon-tgbot
椤圭洰缁撴瀯
tgbot_project/
鈹溾攢鈹€ config/
鈹?  鈹溾攢鈹€ config_logger.yaml
鈹?  鈹溾攢鈹€ config_database.yaml
鈹?  鈹溾攢鈹€ config_secret.yaml
鈹?  鈹斺攢鈹€ config_runtime.db
鈹溾攢鈹€ database/
鈹?  鈹斺攢鈹€ db.py
鈹溾攢鈹€ logger/
鈹?  鈹斺攢鈹€ logger.py
鈹溾攢鈹€ bot.py
鈹溾攢鈹€ commands/
鈹?  鈹溾攢鈹€ user_management.py
鈹?  鈹溾攢鈹€ file_management.py
鈹?  鈹溾攢鈹€ fortune.py
鈹?  鈹斺攢鈹€ twitter_sync.py
鈹斺攢鈹€ requirements.txt

鍏抽敭鏂囦欢瑙ｉ噴

config_logger.yaml - 閰嶇疆鏃ュ織绯荤粺锛屽畾涔夋棩蹇楃骇鍒拰杈撳嚭璺緞绛夈€愬弬鑰僡rkilo_logger_doc.md銆戙€?

config_database.yaml - 鏁版嵁搴撹繛鎺ラ厤缃€愬弬鑰僡rkilo_database_doc.md銆戙€?

config_secret.yaml - 瀛樺偍鏁忔劅淇℃伅濡侫PI瀵嗛挜銆愬弬鑰僡rkilo_config_doc.md銆戙€?

config_runtime.db - 瀛樺偍杩愯鏃跺姩鎬侀厤缃€愬弬鑰僡rkilo_config_doc.md銆戙€?

logger.py - 鏃ュ織妯″潡锛屾敮鎸佸绾ф棩蹇椼€佹棩蹇楄緭鍑轰綅缃帶鍒躲€佹棩蹇椾笂涓嬫枃銆愬弬鑰僡rkilo_logger_doc.md銆戙€?

db.py - 鏁版嵁搴撴ā鍧楋紝鏀寔SQLite/PostgreSQL绛夛紝灏佽浜嗗父鐢ㄧ殑CRUD鎿嶄綔銆愬弬鑰僡rkilo_database_doc.md銆戙€?

浠ｇ爜瀹炵幇
bot.py - 涓荤▼搴忔枃浠?
import logging
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from commands import user_management, file_management, fortune, twitter_sync
from logger.logger import get_logger
from config import config_logger, config_secret, config_database

# 閰嶇疆鏃ュ織
logger = get_logger("tgbot")

def start(update: Update, context):
    update.message.reply_text("浣犲ソ锛佹杩庝娇鐢═GBot锛岃緭鍏?help鏌ョ湅鍛戒护鍒楄〃銆?)
    logger.info("鐢ㄦ埛鍚姩浜咮ot")

def main():
    # 浠庨厤缃腑鍔犺浇Telegram Token
    tg_token = config_secret.TELEGRAM_API_TOKEN
    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher

    # 璁剧疆鍛戒护澶勭悊鍣?
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("fortune", fortune.fortune))
    dispatcher.add_handler(CommandHandler("upload", file_management.upload))
    dispatcher.add_handler(CommandHandler("manage_user", user_management.manage_user))
    dispatcher.add_handler(CommandHandler("sync_twitter", twitter_sync.sync_twitter))

    # 鍚姩Bot
    updater.start_polling()
    logger.info("Bot鍚姩鎴愬姛")

if __name__ == "__main__":
    main()

logger.py - 鏃ュ織妯″潡
import logging
import os
from logging.handlers import RotatingFileHandler
import sys

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 鎺у埗鍙拌緭鍑?
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 鏂囦欢杈撳嚭
    log_file = os.path.join(os.getcwd(), 'logs', 'tgbot.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

user_management.py - 鐢ㄦ埛绠＄悊鍔熻兘
from telegram import Update
from telegram.ext import CallbackContext
from logger.logger import get_logger
from database.db import add_user, get_user

logger = get_logger("user_management")

def manage_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    command = context.args[0] if context.args else None

    if command == "add":
        add_user(user_id)
        update.message.reply_text(f"鐢ㄦ埛 {user_id} 宸叉坊鍔犮€?)
        logger.info(f"娣诲姞鐢ㄦ埛: {user_id}")
    elif command == "get":
        user = get_user(user_id)
        update.message.reply_text(f"鐢ㄦ埛 {user_id}: {user}")
        logger.info(f"鑾峰彇鐢ㄦ埛: {user_id}")
    else:
        update.message.reply_text("鏃犳晥鐨勫懡浠ゃ€?)
        logger.warning(f"鏃犳晥鍛戒护: {command}")

file_management.py - 鏂囦欢涓婁紶绠＄悊鍔熻兘
from telegram import Update
from telegram.ext import CallbackContext
from logger.logger import get_logger

logger = get_logger("file_management")

def upload(update: Update, context: CallbackContext):
    if update.message.document:
        file = update.message.document.get_file()
        file.download(f'files/{update.message.document.file_name}')
        update.message.reply_text(f"鏂囦欢 {update.message.document.file_name} 涓婁紶鎴愬姛锛?)
        logger.info(f"鏂囦欢涓婁紶: {update.message.document.file_name}")
    else:
        update.message.reply_text("璇蜂笂浼犱竴涓枃浠讹紒")
        logger.warning("鐢ㄦ埛娌℃湁涓婁紶鏂囦欢")

fortune.py - 闅忔満鍔熻兘锛堜粖鏃ヨ繍鍔匡級
from telegram import Update
from telegram.ext import CallbackContext
import random

fortunes = [
    "浠婂ぉ鏄釜骞歌繍鐨勪竴澶╋紒",
    "浠婂ぉ鍙兘浼氶亣鍒颁竴浜涙寫鎴橈紝浣嗕細鏈夊ソ杩愮浉闅忋€?,
    "灏忓績璋ㄦ厧锛屼粖澶╁彲鑳芥湁浜涙剰澶栥€?,
    "浠婂ぉ鏄钩鍑＄殑涓€澶╋紝鍋氳嚜宸辩殑浜嬫儏灏卞ソ銆?,
]

def fortune(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(fortunes))

twitter_sync.py - 鍚屾鎺ㄧ壒鎺ㄦ枃
import tweepy
from telegram import Update
from telegram.ext import CallbackContext
from logger.logger import get_logger

logger = get_logger("twitter_sync")

# 閰嶇疆鎺ㄧ壒API
auth = tweepy.OAuth1UserHandler(
    consumer_key='your_consumer_key',
    consumer_secret='your_consumer_secret',
    access_token='your_access_token',
    access_token_secret='your_access_token_secret'
)
api = tweepy.API(auth)

def sync_twitter(update: Update, context: CallbackContext):
    tweets = api.user_timeline(screen_name='your_twitter_handle', count=5)
    for tweet in tweets:
        update.message.reply_text(f"{tweet.user.name}: {tweet.text}")
    logger.info("鍚屾鎺ㄧ壒鎺ㄦ枃")

閰嶇疆鏂囦欢绀轰緥

config_logger.yaml

log_level: INFO
log_file: logs/tgbot.log
rotate: daily
retention_days: 7
json_format: true


config_database.yaml

database:
  type: postgresql
  host: localhost
  port: 5432
  database: tgbot_db
  username: bot_user
  password: ${DB_PASSWORD}


config_secret.yaml

TELEGRAM_API_TOKEN: 'your_telegram_token'

鏁版嵁搴撶鐞嗭紙db.py锛?
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import config_database

DATABASE_URL = f"postgresql://{config_database.database.username}:{config_database.database.password}@{config_database.database.host}:{config_database.database.port}/{config_database.database.database}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def add_user(user_id):
    # 娣诲姞鐢ㄦ埛鍒版暟鎹簱
    pass

def get_user(user_id):
    # 鑾峰彇鐢ㄦ埛淇℃伅
    pass

瀹夎渚濊禆
pip install python-telegram-bot tweepy sqlalchemy psycopg2
## 蹇€熷紑濮?
1. 寤鸿鍒涘缓铏氭嫙鐜骞跺畨瑁呬緷璧栵細
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r tgbot_project/requirements.txt
   ```
2. 鍦?`tgbot_project/config/config_secret.yaml` 涓～鍏?Telegram 浠ュ強 Twitter 鐨勫瘑閽ワ紙涔熷彲浠ラ€氳繃鐜鍙橀噺瑕嗙洊 `${...}` 鍗犱綅绗︼級銆?3. 鏍规嵁闇€瑕佽皟鏁?`tgbot_project/config/config_database.yaml`锛岄粯璁や娇鐢ㄩ」鐩唴鐨?SQLite 鏁版嵁搴撱€?
## 杩愯鏈哄櫒浜?
```bash
python -m tgbot_project.bot
```

棣栨杩愯浼氳嚜鍔ㄥ垵濮嬪寲鏁版嵁搴撳苟鍒涘缓 `data/runtime.db`銆傚懡浠よ鏄庯細

- `/start`锛氬垵濮嬪寲浼氳瘽骞惰嚜鍔ㄦ敞鍐屽綋鍓嶇敤鎴枫€?- `/manage_user register`锛氬皢鑷繁鍔犲叆鐢ㄦ埛琛ㄣ€?- `/manage_user setrole <telegram_id> <member|admin>`锛氱鐞嗗憳淇敼瑙掕壊銆?- `/manage_user remove <telegram_id>`锛氱鐞嗗憳绉婚櫎鐢ㄦ埛銆?- `/manage_user list`锛氱鐞嗗憳鏌ョ湅鐢ㄦ埛鍒楄〃銆?- `/upload` 鎴栫洿鎺ュ彂閫佹枃浠?鍥剧墖锛氫繚瀛樺埌 `files/` 鐩綍銆?- `/fortune`锛氭煡鐪嬩粖鏃ヨ繍鍔匡紙鍚屼竴鐢ㄦ埛姣忓ぉ鍥哄畾缁撴灉锛夈€?- `/sync_twitter [handle]`锛氬悓姝ョ洰鏍囧笎鎴锋渶杩?5 鏉℃帹鏂囥€?
> Twitter 鍔熻兘闇€瑕佸～鍐欏叏閮ㄥ嚟璇侊紝鍚﹀垯浼氭彁绀哄姛鑳芥湭閰嶇疆銆?


机器人被拉入群组后会自动记录新成员与离群成员：首位注册用户会自动成为管理员，退出的成员会在数据库中标记为已退出并记录离开事件。管理员可使用 `/manage_user list` 查看活跃状态。
