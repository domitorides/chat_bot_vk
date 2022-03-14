from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

BASE_PATH = 'files/Ticket.png'
TEMP_PATH = 'files/Roboto-Regular.ttf'
FONT_SIZE = 30
COLOR_FONT = (0, 0, 0, 255)


def generate_ticket(city_from, city_to, date_user, time_user, number_user):

    base_ticket = Image.open(BASE_PATH).convert('RGBA')
    font = ImageFont.truetype(TEMP_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(base_ticket)
    draw.text((380, 350), city_from, font=font, fill=COLOR_FONT)
    draw.text((320, 430), city_to, font=font, fill=COLOR_FONT)
    draw.text((700, 350), date_user, font=font, fill=COLOR_FONT)
    draw.text((750, 430), time_user, font=font, fill=COLOR_FONT)
    draw.text((320, 510), number_user, font=font, fill=COLOR_FONT)

    responce = requests.get(url='https://www.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50?f=y')
    avatar_like_file = BytesIO(responce.content)
    avatar = Image.open(avatar_like_file)

    base_ticket.paste(avatar, (400, 40))

    # for tests
    # with open('files/ticket_test.png', 'wb') as file:
    #     base_ticket.save(file, 'png')

    temp_file = BytesIO()
    base_ticket.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


# generate_ticket('Лондон', 'Токио', '22-08-2021', '13:20', '453256')