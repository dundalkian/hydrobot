import data
import Bot
from fbchat.models import Message, ThreadType



creds = Bot.config()
client = Bot.startupClient(creds['email'], creds['password'])
Bot.send_homie_stats(client, '1802551463181435', ThreadType.GROUP, False)
data.zero_homie()
Bot.send_message(client, "YEET" ,'1802551463181435', ThreadType.GROUP)
