from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Base import Group, Base, Station, User, Settings
import telebot
import json
import time
import datetime

MAX_GROUP_STUDENTS = 2
# НЕ работает походу
# db = MongoClient()['am-cp']

engine = create_engine('sqlite:///kvestinfa.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


with open('keys.json', 'r') as file:
    token = json.loads(file.read())['bot_token']

bot = telebot.TeleBot(token)


def keyboard(key):
    x = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for j in key:
        x.add(*[telebot.types.KeyboardButton(i) for i in j])
    return x


def log_message(message):
    with open('logs.txt', 'a') as logs:
        line = '[' + str(datetime.datetime.now().time()) + ']' + ' ' + \
              str(message.from_user.first_name) + ' ' + \
              str(message.from_user.last_name) + ' ' + \
              '(' + str(message.from_user.username) + '):' + ' ' + \
              message.text + '  ' + str(message.chat.id)
        logs.write(line+'\n')
        print(line)


def check_user_in_bd(message):
    id_u = message.chat.id
    users = session.query(User).all()
    in_bd = False
    for i in users:
        if i.id == id_u:
            in_bd = True
            break
    session.close()
    return in_bd


def check_station_in_bd(number):
    in_bd = False
    stations = session.query(Station).all()
    for i in stations:
        if i.id == number:
            in_bd = True
            break
    session.close()
    return in_bd


def check_group_in_bd(number):
    in_bd = False
    stations = session.query(Group).all()
    for i in stations:
        if i.id == number:
            in_bd = True
            break
    session.close()
    return in_bd

def check_group_on_st(station):
    in_bd = False
    stations = session.query(Group).all()
    for i in stations:
        if i.current_station == station:
            in_bd = True
            break
    session.close()
    return in_bd


def send_message_group(group_number, text):
    group = session.query(Group).filter_by(id=group_number).one()
    users = session.query(User).filter_by(group=group.id).all()
    for u in users:
        bot.send_message(u.id, text)
    session.close()



# Приветственное сообщение
@bot.message_handler(commands=['start'])
def handle_start(message):
    log_message(message)
    is_open = session.query(Settings).filter_by(name='registration').one().status
    if is_open:
        bot.send_message(message.chat.id, 'Привет, организатор 👋🏻\nДля начала тебе нужно зарегистрироваться. Пиши /reg_org N, где вместо N номер твоей станции. Посмотреть всё станции, чтобы узнать свой номер, ты можешь с помощью команды /free')
    else:
        bot.send_message(message.chat.id, 'Привет, первокурсник 👋🏻\nУже совсем скоро тебе предстоит принять участие в традиционном квесте для первокурсников, и я тебе в этом помогу. Но для начала тебе нужно зарегистрироваться. Пиши /reg_user 1**, где вместо 1** твой номер группы')
    session.close()

# Помощь
@bot.message_handler(commands=['help'])
def handle_help(message):
    user_in = check_user_in_bd(message)
    log_message(message)
    if not user_in:
        bot.send_message(message.chat.id, 'Сначала необходимо зарегистрироваться!')
    else:
        user = session.query(User).filter_by(id=message.chat.id).one()
        if not user.type:
            bot.send_message(message.chat.id, 'Ты зарегистрирован, как участник!\n'
                                              'Задача твоей группы пройти как можно больше станций и заработать как можно больше опыта. '
                                              'Зарабатывать больше опыта тебе помогут деньги, чем больше денег, тем быстрее растёт твой опыт. '
                                              'Деньги можно заработать с помощью специальных заданий до начала квеста. Не надо отправлять мне видео и фото выполненных заданий! '
                                              'Проверять их будет @xxxxx, ему и отправляйте, не забудьте только указать номер своей группы и номер выполненного задания.\n'
                                              'Доступные тебе команды:\n'
                                              '/info - результаты твоей группы\n'
                                              '/free - список свободных станций\n'
                                              '/take N - забронировать станцию для прохождения (N - номер станции)\n\n'
                                              'Порядок твоих действий: выбираешь станцию из свободных, бронируешь эту станцию, бежишь к нужному месту, выполняешь необходимые задания и получаешь награду. '
                                              'После 17:00 бронирование станции станет недоступным, поторопись!\n\n'
                                              'По всем дополнительным вопросам обращаться к @menacing_dwarf')
        else:
            bot.send_message(message.chat.id, 'Ты зарегистрирован, как организатор! Доступные тебе команды:\n'
                                              '/station - информация о твоей станции\n'
                                              '/free - список станций\n'
                                              '/reward N - выставить оценку за прохождение текущей команде (от 1 до 10)\n\n'
                                              )
    session.close()

# Регистрация участника
@bot.message_handler(commands=['reg_user'])
def handler_user(message):
    log_message(message)
    try:
        group = int(message.text.split()[1])
    except:
        bot.send_message(message.chat.id, 'Неправильный формат!')
    else:
        x_in = check_group_in_bd(group)
        if not x_in:
            bot.send_message(message.chat.id, 'Неправильный номер группы!')
        else:
            if len(list(session.query(User).filter_by(group=group).all())) >= MAX_GROUP_STUDENTS:
                bot.send_message(message.chat.id, 'В выбранную группу уже нельзя зарегистрироваться!')
            else:
                user = check_user_in_bd(message)
                if not user:

                    user_reg = User(id=message.chat.id, username=message.from_user.username, full_name=message.from_user.first_name + ' ' + 'message.from_user.last_name', type=0, group=group)
                    session.add(user_reg)
                    session.commit()
                    keyboards = keyboard([['/info'], ['/free'], ['/help']])
                    bot.send_message(message.chat.id, 'Поздравляю! 🎉\n'
                                                      'Теперь ты зарегистрирован как участник группы ' + str(group) + '!\n'
                                                      'Пиши /help для получения основной информации.',
                                     reply_markup=keyboards)
                else:
                    bot.send_message(message.chat.id, 'Ты уже зарегистрирован, второй раз это делать не нужно 😉')
    session.close()

# Информация о результатах группы
@bot.message_handler(commands=['info'])
def handler_info(message):
    log_message(message)
    user_in = check_user_in_bd(message)
    if not user_in:
        bot.send_message(message.chat.id, 'Сначала необходимо зарегистрироваться!')
    else:
        user = session.query(User).filter_by(id=message.chat.id).one()
        group_number = user.group
        if check_group_in_bd(group_number):
            group = session.query(Group).filter_by(id=group_number).one()
            if group.current_station != 0:
                current_station = session.query(Station).filter_by(id=group.current_station).one().name
            else:
                current_station = 'нет текущей станции'
            bot.send_message(message.chat.id, 'Группа номер ' + str(group_number) +
                             '\n🚩Текущая станция: ' + current_station +
                             '\n💰Деньги: ' + str(group.money) +
                             '\n✨Опыт: ' + str(group.experience) +
                             '\n⏫Мультипликатор опыта: ' + str(1 + group.money / 100))
        else:
            bot.send_message(message.chat.id, 'У тебя нет группы(')
    session.close()


# Свободные станции
@bot.message_handler(commands=['free'])
def handler_free(message):
    log_message(message)
    is_started = session.query(Settings).filter_by(name='quest').one().is_started
    is_ended = session.query(Settings).filter_by(name='quest').one().is_ended
    is_open = session.query(Settings).filter_by(name='registration').one().status
    if not is_started and not is_open:
        text = 'Квест ещё не начался, потерпи ещё немножко 😉' if not is_ended else 'Квест уже закончен, можешь отдохнуть 😉'
        bot.send_message(message.chat.id, text)
    else:
        stations = list(session.query(Station).filter_by(group=0).all())
        user_in = check_user_in_bd(message)
        if user_in:
            user = session.query(User).filter_by(id=message.chat.id).one()
            if not user.type:
                group = session.query(Group).filter_by(id=user.group).one()
                stations = list(filter(lambda station: station.name not in group.stations, stations))
        answer = "\n\n".join([str(station.id) + '. ' + station.name +
                              '\n📍Расположение: ' + station.geo +
                              '\n🎁Награда: ' + str(station.reward) for station in stations]) if len(stations) > 0 \
            else "Нет свободных станций"
        bot.send_message(message.chat.id, 'Список свободных станций:\n\n' + answer)
    session.close()


# Взять станцию
@bot.message_handler(commands=['take'])
def handler_take(message):
    log_message(message)
    user_in = check_user_in_bd(message)
    if not user_in:
        bot.send_message(message.chat.id, 'Сначала необходимо зарегистрироваться!')
    else:
        user = session.query(User).filter_by(id=message.chat.id).one()
        is_started = session.query(Settings).filter_by(name='quest').one().is_started
        is_ended = session.query(Settings).filter_by(name='quest').one().is_ended
        if not is_started:
            text = 'Квест ещё не начался, потерпи ещё немножко 😉' if not is_ended else 'Квест уже закончен, можешь отдохнуть 😉'
            bot.send_message(message.chat.id, text)
        else:
            group = session.query(Group).filter_by(id=user.group).one()
            if group.current_station != 0:
                bot.send_message(message.chat.id, 'Вы ещё не закончили прохождение предыдущей станции!')
                session.close()
            else:
                try:
                    station_number = int(message.text.split()[1])
                except:
                    bot.send_message(message.chat.id, 'Неправильный формат!')
                else:
                    station_in = check_station_in_bd(station_number)
                    if not station_in:
                        bot.send_message(message.chat.id, 'Неправильный номер станции!')
                    else:
                        station = session.query(Station).filter_by(id=station_number).one()
                        if station.name in group.stations:
                            bot.send_message(message.chat.id, 'Вы уже прошли эту станцию!')
                            session.close()
                            return
                        session.close()
                        group = session.query(Group).filter_by(id=user.group).one()
                        group.current_station = station_number
                        station.group = group.id
                        session.commit()
                        session.close()
                        bot.send_message(message.chat.id, 'Ваша группа успешно зарегистрирована на станцию \"' +
                                                          station.name +
                                                          '\"! Организатор ждёт вас в следующем месте:\n📍' +
                                                          station.geo)
                        org = session.query(User).filter_by(station=station.id).one().id
                        bot.send_message(org, 'Группа ' + str(group.id) + ' была зарегистрирована на вашу станцию!')
    session.close()


# Регистрация организатора
@bot.message_handler(commands=['reg_org'])
def handler_reg_org(message):
    log_message(message)
    is_open = session.query(Settings).filter_by(name='registration').one().status
    if not is_open:
        bot.send_message(message.chat.id, 'Регистрация организаторов закрыта!')
    else:
        try:
            station = int(message.text.split()[1])
        except:
            bot.send_message(message.chat.id, 'Неправильный формат!')
        else:
            x_in = check_station_in_bd(station)
            if not x_in:
                bot.send_message(message.chat.id, 'Неправильный номер станции!')
            else:
                x = session.query(Station).filter_by(id=station).one()
                user_in = check_user_in_bd(message)
                if not user_in:
                    addorg = User(id=message.chat.id, username=str(message.from_user.username), full_name=str(message.from_user.first_name) + ' ' + str(message.from_user.last_name), type=1, station=station)
                    session.add(addorg)
                    session.commit()
                    keyboards = keyboard([['/station'], ['/help']])
                    bot.send_message(message.chat.id, 'Организатор станции \"' + x.name + '\" зарегистрирован! Введите /help для получения основной информации.',
                                     reply_markup=keyboards)
                else:
                    bot.send_message(message.chat.id, 'Ты уже зарегистрирован, второй раз это делать не нужно 😉')
    session.close()


# Информация о станции
@bot.message_handler(commands=['station'])
def handler_station(message):
    log_message(message)
    user_in = check_user_in_bd(message)
    if not user_in:
        bot.send_message(message.chat.id, 'Организатор не зарегистрирован!')
    else:
        user = session.query(User).filter_by(id=message.chat.id).one()
        if user.type != 1:
            bot.send_message(message.chat.id, 'Вы не организатор!')
        else:
            station = session.query(Station).filter_by(id=user.station).one()
            group = session.query(Group).filter_by(current_station=user.station).one()
            current_group = str(group.id) if group else 'пусто'


            bot.send_message(message.chat.id, str(station.id) + '. ' + station.name +
                                              '\nРасположение: ' + station.geo +
                                              '\nТекущая группа: ' + current_group)
    session.close()


# Начислить баллы
@bot.message_handler(commands=['reward'])
def handler_reward(message):
    log_message(message)
    user_in = check_user_in_bd(message)
    if not user_in:
        bot.send_message(message.chat.id, 'Организатор не зарегистрирован!')
    else:
        user = session.query(User).filter_by(id=message.chat.id).one()
        if user.type != 1:
            bot.send_message(message.chat.id, 'Вы не организатор!')
        else:
            station = session.query(Station).filter_by(id=user.station).one()
            in_bd = check_group_on_st(user.station)
            if not in_bd:
                bot.send_message(message.chat.id, 'На вашей станции никого нет!')
            else:
                group = session.query(Group).filter_by(current_station=user.station).one()
                try:
                    points = int(message.text.split()[1])
                    if points < 1 or points > 10:
                        raise Exception
                except:
                    bot.send_message(message.chat.id, 'Неправильный формат!')
                else:
                    reward = station.reward * points / 10 * (1 + group.money / 100)
                    group.experience += reward
                    group.current_station = 0
                    group.stations += ' ' + station.name
                    session.commit()
                    station.group = 0
                    session.commit()
                    bot.send_message(message.chat.id, 'Группе ' + str(group.id) + ' успешно начисленны баллы!')

                    send_message_group(group.id, 'Станция \"' + station.name + '\" успешно пройдена! 🎉'
                                                    '\nОрганизатор поставил вам ' + str(points) + ' баллов.'
                                                    '\nВам было начисленно ' + str(reward) + ' опыта.'
                                                    '\nВыберите новую станцию из списка свободных.')
    session.close()



# Начисление денег
@bot.message_handler(commands=['pay'])
def handler_pay(message):
    user_in = check_user_in_bd(message)
    if user_in:
        user = session.query(User).filter_by(id=message.chat.id).one()
        log_message(message)
        if user.type == 2 or user.type == 1:
            try:
                group_number = int(message.text.split()[1])
                amount = int(message.text.split()[2])
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
            else:
                group = session.query(Group).filter_by(id=group_number).one()
                group.money += amount
                session.commit()

                bot.send_message(message.chat.id, 'Деньги успешно начилены.')
                send_message_group(group_number, 'Поздравляем! Твоей группе было начислено ' + str(amount) + ' монет! Да вы богаты 💰💰💰')
    session.close()


# Рассылка сообщения
@bot.message_handler(commands=['mailing'])
def handler_mailing(message):
    user_in = check_user_in_bd(message)
    if user_in:
        user = session.query(User).filter_by(id=message.chat.id).one()
        log_message(message)
        if user.type == 2 or user.type == 1:
            try:
                text = ' '.join(message.text.split()[1:])
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
            else:
                users = session.query(User).all()
                for u in users:
                    bot.send_message(u.id, text)
    session.close()


# Открыть регистрацию организаторов
@bot.message_handler(commands=['open'])
def handler_open(message):
    log_message(message)
    user = session.query(User).filter_by(id=message.chat.id).one()
    if user.type == 2 or user.type == 1:
        open_settings = session.query(Settings).filter_by(name='registration').one()
        open_settings.status = True
        session.commit()
        bot.send_message(message.chat.id, 'Регистрация успешно открыта!')
    session.close()


# Закрыть регистрацию организаторов
@bot.message_handler(commands=['close'])
def handler_close(message):
    log_message(message)
    user = session.query(User).filter_by(id=message.chat.id).one()
    if user.type == 2 or user.type == 1:
        open_settings = session.query(Settings).filter_by(name='registration').one()
        open_settings.status = False
        session.commit()
        bot.send_message(message.chat.id, 'Регистрация успешно закрыта!!')
    session.close()


# Начать квест
@bot.message_handler(commands=['begin'])
def handler_begin(message):
    log_message(message)
    user = session.query(User).filter_by(id=message.chat.id).one()
    if user.type == 2 or user.type == 1:
        quest_settings = session.query(Settings).filter_by(name='quest').one()
        quest_settings.is_started = True
        quest_settings.is_ended = False
        session.commit()
        bot.send_message(message.chat.id, 'Квест успешно запущен!')
        users = session.query(User).all()
        text = 'Квест только что начался, а значит вы уже можете выбирать станции, выполнять задания и ' \
               'зарабатывать опыт, необходимый для победы!\n' \
               'Поспешите, а то другие группы вас обойдут! 😏'
        for u in users:
            bot.send_message(u.id, text)
    session.close()


# Закончить квест
@bot.message_handler(commands=['end'])
def handler_end(message):
    user = session.query(User).filter_by(id=message.chat.id).one()
    if user.type == 2 or user.type == 1:
        quest_settings = session.query(Settings).filter_by(name='quest').one()
        quest_settings.is_started = False
        quest_settings.is_ended = True
        session.commit()
        bot.send_message(message.chat.id, 'Квест успешно закончен!')
        users = session.query(User).filter_by(type=0).all()
        text = 'Наш квест подощёл к концу, заканчивайте выполнение текущей станции и ждите результатов, ' \
               'которые будут объявлены в клубе! Кстати, вы до сих пор можете приобрести билетики на самую отвязную вечеринку нашего факультета, поспешите 😉, а может уже не можете\n' \
               'А мне пора с вами прощаться и уходить на заслуженный отдых. Было круто проводить с вами время, до новых встреч!!!'
        for u in users:
            bot.send_message(u['id'], text)
    session.close()


# Статистика по всем группам
@bot.message_handler(commands=['stats'])
def handler_stats(message):
    log_message(message)
    user = session.query(User).filter_by(id=message.chat.id).one()
    if user.type == 2 or user.type == 1:
        groups = session.query(Group).all()
        text = 'Рейтинг групп:'
        place = 1
        for group in sorted(groups, key=lambda g: g['experience'], reverse=True):
            text += '\n\n' + str(place) + '. Группа ' + str(group['id']) + \
                    '\nКоличество опыта: ' + str(group['experience']) + \
                    '\nКоличество денег: ' + str(group['money'])
            place += 1

        bot.send_message(message.chat.id, text)
    print('User \"' + message.from_user.username + '\" send message ' + message.text)
    session.close()


# Левое сообщение
@bot.message_handler(content_types=['text'])
def handle_message(message):
    log_message(message)
    bot.send_message(message.chat.id, 'К сожалению, я слишком глупый, чтобы поболтать с тобой 😟')


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(5)
