import json
import os
import time
import datetime
from configparser import ConfigParser
import re

from fbchat import Client, log
from fbchat.models import Message, ThreadType

import data

def config(filename='config.ini', section='facebook credentials'):
    # create a parser 
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section
    creds = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            creds[param[0]] = param[1]
    elif os.environ['EMAIL']: 
        creds['email'] = os.environ['EMAIL']
        creds['password'] = os.environ['PASSWORD']
    else:
        raise Exception(
            'Section {0} not found in the {1} file'.format(section, filename))
    return creds


class HydroBot(Client):
    all_homies = []
    current_homie_chad = ''
    def pmMe(self, txt):
        self.send(Message(text = txt), thread_id = client.uid, thread_type=ThreadType.USER)

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if message_object.text is not None and (thread_id == '1802551463181435' or thread_type == ThreadType.USER):
            messageText = message_object.text.lower()
            if re.match("(?i)hydro", messageText):
                process_message(self, author_id, messageText, thread_id, thread_type)
            elif messageText == client.fetchThreadInfo(thread_id)[thread_id].emoji:
                process_message(self, author_id, messageText, thread_id, thread_type)
        super(HydroBot, self).onMessage(author_id=author_id, message_object=message_object, thread_id=thread_id, thread_type=thread_type, **kwargs)



def process_message(self, author_id, messageText, thread_id, thread_type):
    if author_id != self.uid:
        print(messageText)
        user = self.fetchUserInfo(author_id)[author_id]
        name = user.name
        add_homie(self, thread_id, thread_type, author_id, name, 0)
        if re.search("(?i)help", messageText):
            txt = """
hydro stats (-v|full|verbose)- lists stats since last reset. Verbose options available
hydro set [num] - set your bottle size (give in mL)
hydro decrement - decrement by one bottle amount
{} - tap emoji to increment by one bottle amount
""".format(client.fetchThreadInfo(thread_id)[thread_id].emoji)
            self.send(Message(text = txt), thread_id=thread_id, thread_type=thread_type)
        elif re.search("(?i)set", messageText):
            iterator = re.finditer(r"(?<=\bset\s)([0-9]+)", messageText)
            match = next(iterator)
            size = match[0]
            update_homie(self, thread_id, thread_type, author_id, name, size)
        elif re.search("(?i)stats", messageText):
            if re.search("(-v|full|verbose)", messageText):
                send_homie_stats(self, thread_id, thread_type, True)
            else:
                send_homie_stats(self, thread_id, thread_type, False)
        elif re.search("(?i)decrement", messageText):
            homie_decrement(self, thread_id, thread_type, author_id)
        elif messageText == client.fetchThreadInfo(thread_id)[thread_id].emoji:
            homie_increment(self, thread_id, thread_type, author_id)
        elif re.search("(?i)yeet", messageText) and author_id == '100002237228114':
            homie_zero(self, thread_id, thread_type)
        elif re.search("(?i)all", messageText):
            all_data = data.get_drinks()
            times = [i[2] for i in all_data]




def homie_zero(self, thread_id, thread_type):
    data.zero_homie()

def homie_increment(self, thread_id, thread_type, author_id):
    data.increment_homie(author_id)
    data.insert_drink(author_id)

def homie_decrement(self, thread_id, thread_type, author_id):
    data.decrement_homie(author_id)
    data.delete_last_drink(author_id)

def send_homie_stats(self, thread_id, thread_type, verbose=False):
    stats = data.get_homies()
    stats.sort(key=lambda x: ((x[2]*x[3])/1000), reverse=True)
    stats = filter(lambda x: x[1] != 'AssumeZero Bot', stats)
    
    string = "Hydration stats since midnight as follows:"
    for s in stats:
        if verbose:
            string = string + "\n - {} drank {}L ({} bottles, each {}mL in size.)".format(s[1], (s[2]*s[3])/1000 ,s[3], s[2] )
        else:
            string = string + "\n - {}: {}L".format(s[1], (s[2]*s[3])/1000)
    self.send(Message(text = string), thread_id = thread_id, thread_type=thread_type)

def update_homie(self, thread_id, thread_type, fbid, name, size):
    homie = [fbid, name, size, 0]
    data.update_homie(homie)
    txt = "Updated bottle size to {}ml".format(size)
    self.send(Message(text = txt), thread_id = thread_id, thread_type = thread_type)

def add_homie(self, thread_id, thread_type, fbid, name, size):
    homie = [fbid, name, size, 0]
    data.insert_homie(homie)


def startupClient(email, password):
    try:
        with open("session.txt", "r") as session:
            session_cookies = json.loads(session.read())
    except FileNotFoundError:
        session_cookies = None

    client = HydroBot(email, password, session_cookies=session_cookies)
    with open("session.txt", "w") as session:
        session.write(json.dumps(client.getSession()))
    return client


### Reving up the engines ###
creds = config()
client = startupClient(creds['email'], creds['password'])
client.listen()
