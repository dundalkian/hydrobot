from fbchat_muqit import Client, Message, ThreadType, MessageReaction
import asyncio
import sys
from datetime import datetime
# Project imports
import data
# Create a class use Client as base Class

def send_message(self, txt, thread_id, thread_type):
    self.send(Message(text=txt), thread_id=thread_id, thread_type=thread_type)

def add_homie(self, thread_id, thread_type, fbid, name, size):
    data.insert_homie(fbid, name)

async def homie_increment(self, thread_id, thread_type, author_id, message_object):
    data.insert_drink(author_id)
    #await message_object.react(str(MessageReaction.YES))
    await self.reactToMessage(message_object.uid, MessageReaction.YES)

async def homie_decrement(self, thread_id, thread_type, author_id, message_object):
    data.delete_last_drink(author_id)
    #await message_object.react(str(MessageReaction.YES))
    await self.reactToMessage(message_object.uid, MessageReaction.YES)

def get_homie_bottles(self, thread_id, thread_type, fb_id):
    string = "Your Bottles:"
    selected = data.get_bottle(fb_id)
    bottles = data.get_bottle_stats(fb_id)
    bottles = sorted(filter(lambda x: x[1] != 'NULL', bottles), key=lambda x: x[3], reverse=True)
    for b in bottles:
        indic = '-' if b[0] != selected else '🍼'
        string += "\n {} {} : {}mL : {} total drinks".format(indic, b[1], b[2], b[3])
    return string
    #self.send(Message(text=string), thread_id = thread_id, thread_type=thread_type) 


def homie_stats(fb_id, time_string):
    # All the bottles registered to a person
    bottles = dict(data.get_bottle_ids(fb_id))
    
    # Every event for person within timespan but only the bottle ids
    events_as_bottle_ids = [i for (i,) in data.get_homie_events_over_time(fb_id, time_string)]
    total = 0
    sums = len(events_as_bottle_ids)
    for e in events_as_bottle_ids:
        total = total + bottles[e]
        if bottles[e] == 0:
            sums = sums-1
    return [total/1000, sums]


def group_stats(time_string='1 day', verbose=False):
    homies = dict(data.get_homie_list())
    homie_results = []
    string = "Hydration Stats over the past {}:".format(time_string)
    for hid in homies:
        stats = homie_stats(hid, time_string)
        homie_results.append([homies[hid], stats[0], stats[1]])

    homie_results.sort(key=lambda x: (x[1]),reverse=True)
    homie_results = filter(lambda x: x[0] != 'AssumeZero Bot', homie_results)
    king_quota = 1
    for h in homie_results:
        if verbose:
            string = string + "\n - {} drank {}L (finishing {} bottles total in the past {})".format(h[0], h[1], h[2], time_string)
        else:
            if h[1] < 2.0:
                string = string + "\n 🥵 "
            elif king_quota > 0:
                string = string + "\n 👑 "
                king_quota = 0
            else:
                string = string + "\n 👍 "
            string = string + "{}: {}L".format(h[0], h[1])
    return string
    #self.send(Message(text=string), thread_id = thread_id, thread_type=thread_type) 

class HydroBot(Client):

    async def onMessage(self, mid, author_id: str, message_object: Message, thread_id, thread_type=ThreadType.USER, **kwargs):
        if author_id != self.uid and message_object.text is not None and (thread_id == '1802551463181435' or thread_id == '2813871368632313'):
            messageText = message_object.text
            ma = messageText.split() # message array
            thread_emoji = await self.get_thread_emoji(thread_id)
            if ma[0].lower() == "physics":
                print(f"Message was meant for physics: {messageText}")
                await self.process_message(mid, author_id, ma, thread_id, thread_type, message_object)
                #await message_object.react(thread_emoji)
            elif messageText == thread_emoji:
                print(f"Message was an emoji: {messageText}")
                await homie_increment(self, thread_id, thread_type, author_id, message_object)
            else:
                print(f"Message was not meant for the bot: {messageText}")
        #super(HydroBot, self).onMessage(mid=mid, author_id=author_id, message_object=message_object, thread_id=thread_id, thread_type=thread_type, **kwargs)

        """you will receive all messenger messages here every time anyone sends messages in a thread (Group/User)"""
        # author_id is message sender ID
        # if author_id != self.uid:
        #     await message_object.reply("Hello! This is a reply")
        #     await message_object.react("❤️")
        #     # mid is message ID
        #     await self.sendMessage("Hello", thread_id, thread_type, reply_to_id=mid)
    
    async def get_thread_emoji(self, thread_id):
        thread_info = await self.fetchThreadInfo(thread_id)
        thread_emoji = thread_info[thread_id].emoji
        return thread_emoji
    
    async def process_message(self, mid, author_id, ma, thread_id, thread_type, message_object):
        response = ""
        if author_id != self.uid:
            user_info = await self.fetchUserInfo(author_id)
            user = user_info[author_id]
            name = user.name
            try:
                data.insert_homie(author_id, name) # TODO: Use add_homie() instead of this, this line just replaces that.
            except:
                pass
            if ma[1] == "help":
                txt = """
physics stats ([num] [interval]) (-v|full|verbose)- lists stats
-> "physics stats 1 day full"
-> "physics stats"
-> "physics stats 35 minutes"
-> "physics stats -v"
physics add [name] [num] - add a bottle (!!no whitespace!!) and its size (give in mL)
physics remove [name] - remove your bottle called [name] (Warning, will delete all drink events made with this bottle)
physics switch [name] - switch your current bottle to the bottle with [name].
physics drink [name] - logs a single drink with bottle [name], does not change current bottle
physics rename [name] [newname] - rename a bottle
physics list - shows all of your bottles
physics decrement - remove the last drink event
{} - tap emoji to log a drink, uses your current bottle

Note: You must add a bottle to get started (old db got wiped). Measure it in mL.

Recommended daily intake is over 2 liters of water! Hydrate or Diedrate!
    """.format(await self.get_thread_emoji(thread_id))
                await self.send(Message(text = txt), thread_id=thread_id, thread_type=thread_type)
            elif ma[1] == "add" and str.isdigit(ma[3]):
                data.insert_bottle(ma[2], ma[3], author_id)
                await self.reactToMessage(message_object.uid, MessageReaction.YES)
            elif ma[1] == "remove":
                data.delete_bottle(ma[2], author_id)
                await self.reactToMessage(message_object.uid, MessageReaction.YES)
            elif ma[1] == "switch":
                data.switch_bottle(ma[2], author_id)
                await self.reactToMessage(message_object.uid, MessageReaction.YES)
            elif ma[1] == "rename":
                data.rename_bottle(ma[2], ma[3], author_id)
                await self.reactToMessage(message_object.uid, MessageReaction.YES)
            elif ma[1] == "list":
                response = get_homie_bottles(self, thread_id, thread_type, author_id)
            elif ma[1] == "decrement" or ma[1] == "dec":
                await homie_decrement(self, thread_id, thread_type, author_id, message_object)
            elif ma[1] == "increment" or ma[1] == "inc":
                await homie_increment(self, thread_id, thread_type, author_id, message_object)
            elif ma[1] == "drink":
                data.insert_drink(author_id, bottle_name=ma[2])
                await self.reactToMessage(message_object.uid, MessageReaction.YES)
            elif ma[1] == "stats":
                verbose_list = ["-v", "full", "verbose", "--verbose"]
                if len(ma)>2 and ma[2] in verbose_list:
                    response = group_stats(verbose=True)
                elif len(ma)>3 and str.isdigit(ma[2].replace(".", "", 1)) and ma[3] in ["second","minute","hour","day","month","year","seconds","minutes","hours","days","months","years"]:
                    ts = "{} {}".format(ma[2], ma[3])
                    if len(ma)>4 and ma[4] in verbose_list:
                        response = group_stats(time_string=ts, verbose=True)
                    else:
                        response = group_stats(time_string=ts, verbose=False)
                else:
                    response = group_stats(verbose=False)
            
            if response:
                await self.sendMessage(response, thread_id, thread_type, reply_to_id=mid)
    

async def main():
    cookies_path = "ufc-facebook.json"
    bot = await HydroBot.startSession(cookies_path)
    if await bot.isLoggedIn():
        fetch_client_info = await bot.fetchUserInfo(bot.uid)
        client_info = fetch_client_info[bot.uid]
        print("Logged in as", client_info.name)
        print(f"Group Stats: {group_stats()}")

    try:
        await bot.listen()
    except Exception as e:
        print(e)


while True:
    current_time = datetime.now()
    # Windows User uncomment below two lines
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print(f"Restarting.... {current_time}")
    asyncio.run(main())