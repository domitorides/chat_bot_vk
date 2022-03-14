from pony.orm import Database, Required, Json

from chatbot.settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя внутри сценария"""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class InfoTicket(db.Entity):
    """Данные по билету"""
    city_from = Required(str)
    city_to = Required(str)
    date_user = Required(str)
    time_user = Required(str)
    number_user = Required(str)
    comment_user = Required(str)
    tel_number = Required(str)


db.generate_mapping(create_tables=True)