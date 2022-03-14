
import random
import logging

import requests
from pony.orm import db_session

import handlers
from chatbot.models import UserState, InfoTicket

try:
    import settings
except ImportError:
    exit('Do cp settings.py.default settings.py and set token')

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotMessageEvent

log = logging.getLogger('bot')


def configure_logging():

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler("bot.log")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    log.setLevel(logging.DEBUG)


class Bot:
    """
    Echo bot для vk.com

    Use python 3.9
    """

    def __init__(self, group_id, token):
        """
        group_id: id группы в вк
        token: секретный токен
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """
        Запуск бота.
        """
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception("Ошибка в обработке сообщения")

    @db_session
    def on_event(self, event):
        """
        Отправляет сообщение назад, если это текст

        event: VkBotMessageEvent object
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Пока нет обработки такого типа %s', event.type)
            return

        user_id = event.object.message['peer_id']
        text = event.object.message['text']

        state = UserState.get(user_id=str(user_id))

        if state is not None:
            # continue scenario
            if text == '/ticket' or text == '/help':
                state.delete()
                self.search_intents(text, user_id)
            else:
                self.continue_scenario(text, state, user_id)
        else:
            # search intent
            self.search_intents(text, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']

        attachment = f'photo{owner_id}_{media_id}'

        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id
        )

    def send_step(self, step, user_id, text, context):

        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, scenario_name, user_id, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})

    def search_intents(self, text, user_id):
        check = 0
        for intent in settings.INTENTS:
            if text in intent['tokens']:
                check = 1
                # run intent
                if intent['answer']:
                    text_to_send = intent['answer']
                    self.send_text(text_to_send, user_id)
                else:
                    self.start_scenario(intent['scenario'], user_id, text)
        if check == 0:
            self.send_text(settings.DEFAULT_ANSWER, user_id)

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])

        choose = handler(text=text, context=state.context)

        if handler(text=text, context=state.context):
            # next step
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)

            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                InfoTicket(city_from=state.context['city_from'],
                           city_to=state.context['city_to'],
                           date_user=state.context['date_user'],
                           time_user=state.context['time_user'],
                           number_user=state.context['number_user'],
                           comment_user=state.context['comment_user'],
                           tel_number=state.context['tel_number'])
                state.delete()

        elif state.step_name == 'step2' and choose is None:
            text_to_send = step['failure_text_noway']
            self.send_text(text_to_send, user_id)
            state.delete()
        elif state.step_name == 'step7' and choose is None:
            text_to_send = f'Можно попробывать ещё раз, введите команду /ticket для повторной попытки'
            self.send_text(text_to_send, user_id)
            state.delete()

        else:
            # retry current step
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()