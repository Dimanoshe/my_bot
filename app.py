from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import vk_api
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import requests
import time
import random


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.bd'  # Выбор БД в данном случае - sqlite и название
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)        # добавление запускаемого файла (этого) в бд


class Bbase(db.Model):   # Создание колонок в бд + параметры
    id = db.Column(db.Integer, primary_key=True)
    bot_request = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    date_of_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Bbasee %r>" % self.id


bot_base = Bbase.query.order_by(Bbase.date_of_creation).all()
#for i in bot_base:
    #print(i.bot_request, '-----', i.bot_response)


with open('token') as f:
    token = f.readline()

otvet = []
print('start')
session = requests.Session()
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
session_api = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, "193971503")
resp = None

"""
ф-я отправки сообщения в чат или личные сообщения.
"""


def send_message():
    if event.from_user:
        # print('whear 1')
        # print(vk.messages.send)
        print('test info: ' + str(event.object.get('message').get('from_id')))
        print(event)
        vk.messages.send(
            user_id=event.object.get('message').get('peer_id'),
            random_id=get_random_id(),
            message=message)
    if event.from_chat:
        # print('whear 2')
        # print('test info: ' + str(event.object.get('message').get('peer_id')))
        vk.messages.send(
            chat_id=event.chat_id,
            random_id=get_random_id(),
            message=message)



"""
Цикл с ожиданием события, в данном случае это отправка сообщения,
пока сообщения нет - ничего не происходит, после появления сообщения цикл запускается, и после исполнения
ждет следующее сообщение. 
"""

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        resp = event.object.get('message').get('text').lower()

        if len(resp) >= 2 and resp[:2] != '==' and resp[:5] != 'удали':
            print(type(resp))
            print('message: ', resp)
            with open('dialog.txt', 'a', encoding='utf8') as f:
                f.write('\nПользователь: ' + resp)
            if resp[-1] == '?' or resp[-1] == '!':
                resp = resp[:-1]


            for i in bot_base:
                i.bot_request = i.bot_request.lower()
                if i.bot_request == resp:
                    otvet.append(str(i.bot_response) + ' ID = ' + str(i.id))
            print(otvet)

            if len(otvet) >= 1:
                message = random.choice(otvet)
                with open('dialog.txt', 'a', encoding='utf8') as f:
                    f.write('\nБот ' + message)
                message = message[:message.find('ID') - 1]
                send_message()
            else:
                otvet = ['ЧирИк...', 'Напписанно что-то неонятное, так что я хз...',
                             'попробуй написать что то более тривиальное...',
                             'сложна, лучше бы попросил аник рассказать...',
                             'Я тебе не нейросеть, давай по нашински, по ботски!',
                             'Не знаю что ответить на это...',
                             'Этого запроса нет в моей базе...', 'Я просто поЧирИкаю на это',
                             'бла-бла-бла...(не понимат)', 'Я не очень умный, давай другое...']
                print(otvet)
                message = random.choice(otvet)
                with open('dialog.txt', 'a', encoding='utf8') as f:
                    f.write('\nБот ' + message)
                send_message()
            otvet.clear()

        elif resp[:2] == '==':
            with open('dialog.txt', 'a', encoding='utf8') as f:
                f.write('\nОбучение: ' + resp)
            resp = resp[2:]
            if resp.find('=') >= 0:
                resp = resp.split('=')

                db.session.add(Bbase(bot_request=resp[0], bot_response=resp[1]))
                db.session.commit()

                print('   обучение   ' + str(resp))
                message = 'База ответов обновлена.'
                with open('dialog.txt', 'a', encoding='utf8') as f:
                    f.write('\nБот ' + message)
                send_message()

        elif resp[:5] == 'удали':
            resp = resp.split()
            db.session.delete(Bbase.query.get_or_404(resp[1]))
            db.session.commit()
            with open('dialog.txt', 'a', encoding='utf8') as f:
                f.write('\nУдаление' + str(resp[1]))
            message = 'Удаление прощло успешно!'
            send_message()

        else:
            message = 'Ничего не произошло, ЧиРик!'
            send_message()