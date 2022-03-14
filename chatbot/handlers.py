import re

import settings
import datetime

from chatbot.generate_ticket import generate_ticket

re_data = re.compile(r'\d{2}-\d{2}-\d{4}')
re_number = re.compile(r'(8|\+7)\d{10}')


DATA_LIST = ['Monday',  'Tuesday', 'Wednesday',  'Thursday',  'Friday', 'Saturday', 'Sunday']
re_data1 = re.compile(r'[0-9]{1,2}')


def dispatcher(city_from, city_to, date_user):
    set_1 = []
    for data in settings.FLIGHTS:
        choose = 0
        list_date1 = []
        if data['city_from'] == city_from and data['city_to'] == city_to:
            if data['date'] in DATA_LIST:
                choose = 1
            elif '-' not in data['date']:
                choose = 2

            if choose == 1:
                i = 0
                day, month, year = (int(x) for x in date_user.split('-'))
                ans = datetime.date(year, month, day)
                while i < 5:
                    if ans.strftime("%A") in data['date']:
                        list_date1.append(ans.strftime("%d-%m-%Y"))
                        i += 1
                    ans = ans + datetime.timedelta(days=1)
                time = data['date_time']
                number = data['number']
                set_1.append({"city_from": city_from, "city_to": city_to, "list_date": list_date1, "time": time,
                              "number": number})

            elif choose == 2:
                i = 0
                day, month, year = (int(x) for x in date_user.split('-'))
                ans = datetime.date(year, month, day)
                while i < 5:
                    list_check = re.findall(re_data1, data['date'])
                    for date in list_check:
                        if ans.day == int(date):
                            list_date1.append(ans.strftime("%d-%m-%Y"))
                            i += 1
                            continue
                    ans = ans + datetime.timedelta(days=1)
                time = data['date_time']
                number = data['number']
                set_1.append({"city_from": city_from, "city_to": city_to, "list_date": list_date1, "time": time,
                              "number": number})
    if set_1:
        all_date = []
        for data in set_1:
            for date in data["list_date"]:
                all_date.append((date, data["time"], data["number"]))
        all_date = sorted(all_date, key=lambda d: datetime.datetime.strptime(d[0], '%d-%m-%Y'))
        all_date = all_date[:5]

        return all_date
    else:
        return False


def handler_city_from(text, context):
    for city in settings.CITYS:
        if text.lower() == city.lower():
            context['city_from'] = city
            return True
    else:
        return False


def handler_city_to(text, context):
    for city in settings.CITYS:
        if text.lower() == city.lower():
            for data in settings.FLIGHTS:
                if data['city_from'].lower() == context['city_from'].lower() and data['city_to'].lower() == text.lower():
                    context['city_to'] = data['city_to']
                    return True
            else:
                return None
    else:
        return False


def handler_data(text, context):
    match = re.match(re_data, text)
    if match:
        context['date'] = text
        text_to_send = str()

        info = dispatcher(context['city_from'], context['city_to'], context['date'])
        cnt = 1
        for data in info:
            text_to_send += f"Рейс {cnt}:\nДата: {data[0]} Время: {data[1]},  Рейс: {data[2]}\n"
            cnt += 1
        context['flights'] = text_to_send
        return True
    else:
        return False


def handler_number(text, context):
    info = dispatcher(context['city_from'], context['city_to'], context['date'])
    cnt = 1
    if text.isdigit() and 5 >= int(text) >= 1:
        for data in info:
            if cnt == int(text):
                context['date_user'] = data[0]
                context['time_user'] = data[1]
                context['number_user'] = data[2]
                return info
            cnt += 1
    else:
        return False


def handler_places(text, context):
    if text.isdigit() and 5 >= int(text) >= 1:
        context['places'] = text
        return True
    else:
        return False


def handler_check(text, context):
    if 'да' in text:
        return text
    elif 'нет' in text:
        return None
    else:
        return False


def handler_comment(text, context):
    context['comment_user'] = text
    return True


def handler_tel_number(text, context):
    match = re.match(re_number, text)
    if match:
        context['tel_number'] = text
        return True
    else:
        return False


def generate_ticket_handler(text, context):
    return generate_ticket(city_from=context['city_from'], city_to=context['city_to'],
                           date_user=context['date_user'], time_user=context['time_user'],
                           number_user=context['number_user'])
