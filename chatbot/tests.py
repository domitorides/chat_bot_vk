import datetime
import unittest
from copy import deepcopy
from unittest.mock import patch, Mock

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

import settings
from bot import Bot
from freezegun import freeze_time

from chatbot.generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


class Test1(unittest.TestCase):

    RAW_EVENT = {
        'type': 'message_new', 'object':
            {'message':
                 {'date': 1624879783, 'from_id': 168414955, 'id': 118, 'out': 0,
                  'peer_id': 168414955, 'text': 'f', 'conversation_message_id': 105,
                  'fwd_messages': [], 'important': False, 'random_id': 0, 'attachments': [], 'is_hidden': False},
             'client_info':
                 {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                     'intent_subscribe', 'intent_unsubscribe'],
                  'keyboard': True, 'inline_keyboard': True, 'carousel': True, 'lang_id': 0}
             },
        'group_id': 203372699, 'event_id': '7a0689d0529ba65b6eafe236687c7386e34d7573'}

    def test_ok(self):
        count = 5
        obj = {}
        events = [obj] * count

        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    INPUTS = [
        'kfekfk',
        '/help',
        '/ticket',
        'gregr',
        'Лондон',
        'gsgsrg',
        'Токио',
        '19-059-2021',
        '12-12-2012',
        '65',
        '2',
        '0',
        '3',
        'text',
        'да',
        '343252',
        '88005553535'
    ]

    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.SCENARIOS['booking_tickets']['steps']['step1']['text'],
        settings.SCENARIOS['booking_tickets']['steps']['step1']['failure_text'],
        settings.SCENARIOS['booking_tickets']['steps']['step2']['text'],
        settings.SCENARIOS['booking_tickets']['steps']['step2']['failure_text'],
        settings.SCENARIOS['booking_tickets']['steps']['step3']['text'],
        settings.SCENARIOS['booking_tickets']['steps']['step3']['failure_text'],
        settings.SCENARIOS['booking_tickets']['steps']['step4']['text'].format(
            flights= f"Рейс 1:\nДата: 19-09-2021 Время: 13:20,  Рейс: 453256\n"
                     f"Рейс 2:\nДата: 20-09-2021 Время: 11:40,  Рейс: 132340\n"
                     f"Рейс 3:\nДата: 24-09-2021 Время: 15:40,  Рейс: 132323\n"
                     f"Рейс 4:\nДата: 26-09-2021 Время: 13:20,  Рейс: 453256\n"
                     f"Рейс 5:\nДата: 01-10-2021 Время: 15:40,  Рейс: 132323\n",
        ),
        settings.SCENARIOS['booking_tickets']['steps']['step4']['failure_text'],
        settings.SCENARIOS['booking_tickets']['steps']['step5']['text'],
        settings.SCENARIOS['booking_tickets']['steps']['step5']['failure_text'],
        settings.SCENARIOS['booking_tickets']['steps']['step6']['text'],
        settings.SCENARIOS['booking_tickets']['steps']['step7']['text'].format(
            date_user='20-09-2021',
            time_user='11:40',
            number_user='132340',
            places='3',
            comment_user='text'
        ),
        settings.SCENARIOS['booking_tickets']['steps']['step8']['text'],
        settings.SCENARIOS['booking_tickets']['steps']['step8']['failure_text'],
        settings.SCENARIOS['booking_tickets']['steps']['step9']['text'],
    ]

    @freeze_time("2021-09-19")
    @isolate_db
    def test_run_ok(self):

        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        time = datetime.datetime.now()
        time = time.strftime("%d-%m-%Y")
        self.INPUTS[8] = time

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        # for r, e in zip(real_outputs, self.EXPECTED_OUTPUTS):
        #     print(f'{r}--------------------{e}')
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_generation_image(self):

        with open('files/req_get.jpeg', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket('Лондон', 'Токио', '22-08-2021', '13:20', '453256')

        with open('files/ticket_test.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes


