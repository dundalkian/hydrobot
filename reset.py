import data
import Bot
from fbchat.models import Message, ThreadType


data.zero_homie()
creds = Bot.config()
client = Bot.startupClient(creds['email'], creds['password'])
Bot.send_message(client, "YEET" ,'1802551463181435', ThreadType.GROUP)
