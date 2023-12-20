import sqlite3
import telebot
import requests
from telebot import types
from random import randint

Token = '6828169517:AAG0AbnPSw1Y4g_mnCYIQeUf5z6eW8m42v8'
api_key = '85a8fa826a63403bab28c51a2e679579'

bot = telebot.TeleBot(Token)
main_url = None
country = None
time = None
keyword = None


@bot.message_handler(commands=['start'])
def start(message):
    """
    Callback menu if user clicks the button "Get news"
    :param message: Received command /start
    :type message: telebot.types.Message
    """
    database = sqlite3.connect('Keyword.sql')
    cursor = database.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Keywords (
    Word TEXT PRIMARY KEY,
    count INTEGER NOT NULL )
    ''')

    database.commit()
    cursor.close()
    database.close()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Get news', callback_data='menu'))
    bot.send_message(message.chat.id, 'Добро пожаловать на новостной бот ViNewsBot!\n'
                                      'Для того, чтобы получить новость, '
                                      'вы можете нажимать на кнопку: "Get news"',  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('menu'))
def menu(call):
    """
    Show the buttons where the user can choose their news
    :param call: message that was received with using callback menu
    :type: telebot.types.CallbackQuery
    """
    menu0 = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    btn1 = types.KeyboardButton('Random news')
    btn2 = types.KeyboardButton('News with keyword')
    btn3 = types.KeyboardButton('News with main keyword')
    menu0.add(btn1)
    menu0.add(btn2, btn3)
    bot.send_message(call.message.chat.id, 'Можете выбрать из ниже перечисленных новостей:\n'
                                           'Random news - рандомная новость,'
                                           'где можно выбрать конекретную дату \n'
                                           'News with keyword - новость через ключевого слова\n'
                                           'News with main keyword - новость по частоте ключевого слова.',
                     reply_markup=menu0)
    bot.register_next_step_handler(call.message, information)


def information(message):
    """

    :param message:
    :type:
    :return:
    """
    answer = message.text
    if answer == 'Random news':
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('Русский', callback_data='ru'))
        markup.row(types.InlineKeyboardButton('Английский', callback_data='us'))
        bot.send_message(message.chat.id, 'Введите на какокм языке хотите прочитать текст:', reply_markup=markup)
    elif answer == 'News with keyword':
        bot.send_message(message.chat.id, 'Введите ключевое слово:')
        bot.register_next_step_handler(message, gainer2)
    elif answer == 'News with main keyword':
        global keyword
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        database = sqlite3.connect('Keyword.sql')
        cursor = database.cursor()
        cursor.execute("SELECT * FROM Keywords")
        data = cursor.fetchall()
        if len(data) > 0:
            cursor.execute("SELECT MAX(count) FROM Keywords")
            cursor.execute("SELECT word FROM Keywords WHERE count = ?", (cursor.fetchall()[0]))
            word = cursor.fetchall()
            if len(word) == 1:
                keyword = word[0][0]
                markup.add(types.KeyboardButton(word[0][0]))
                bot.send_message(message.chat.id, 'Main keywords', reply_markup=markup)
            else:
                for i in range(len(word)):
                    markup.add(types.KeyboardButton(word[i][0]))
                bot.send_message(message.chat.id, 'Main keywords', reply_markup=markup)
            bot.register_next_step_handler(message, gainer2)

        else:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('Вернуться в меню', callback_data='menu')
            markup.add(btn1)
            bot.send_message(message.chat.id, 'В базе данных нет ключевых слов: получите через новость с ключом',
                             reply_markup=markup)
        cursor.close()
        database.close()


@bot.callback_query_handler(func=lambda msg: msg.data.startswith('ru') or msg.data.startswith('us'))
def gainer1(msg):
    """

    :param msg:
    :return:
    """
    if msg.data == 'ru' or msg.data == 'us':
        global country, main_url
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Select time', callback_data='Select'))
        markup.add(types.InlineKeyboardButton('Skip time', callback_data='Skip'))
        country = 'country=' + msg.data
        main_url = f'https://newsapi.org/v2/top-headlines?{country}&apiKey={api_key}'
        bot.send_message(msg.message.chat.id, 'Время', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('Select') or call.data.startswith('Skip'))
def gainer1_1(call):
    """

    :param call:
    :return:
    """
    if call.data == 'Select':
        bot.send_message(call.message.chat.id, 'Хотите выбрать промежуток времени или точную дату?\n'
                                               'Если да, то введите в строке дату (Пример: '
                                               'ГОД/МЕСЯЦ/ДЕНЬ)\n'
                                               'Если нет, то нажмите на кнопку отмену')
        bot.register_next_step_handler(call.message, gainer1_2)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(types.KeyboardButton('✅Done'))
        bot.send_message(call.message.chat.id, 'Портвердите', reply_markup=markup)
        bot.register_next_step_handler(call.message, news)


def gainer1_2(message):
    """

    :param message:
    :return:
    """
    global time, country, main_url
    time = '&from=' + message.text
    main_url = f'https://newsapi.org/v2/top-headlines?{country}{time}&apiKey={api_key}'
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton('✅Done'))
    bot.send_message(message.chat.id, 'Портвердите', reply_markup=markup)
    bot.register_next_step_handler(message, news)


def gainer2(message):
    """

    :param message:
    :return:
    """
    global keyword, main_url
    keyword = 'q=' + message.text
    if len(message.text.split(' ')) == 1:
        main_url = f'https://newsapi.org/v2/everything?{keyword}&apiKey={api_key}'
        post = requests.get(main_url).json()
        if post['totalResults'] > 0:
            database = sqlite3.connect('Keyword.sql')
            cursor = database.cursor()
            word = message.text
            cursor.execute("SELECT * FROM Keywords")
            data = cursor.fetchall()
            array = [data[int(i)][0] for i in range(len(data))]
            c = [data[int(i)][1] for i in range(len(data))]
            if word in array:
                cursor.execute("""Update Keywords set count = ? where word = ?""", (c[array.index(word)] + 1, word))
            else:
                cursor.execute('''INSERT INTO Keywords (word, count) VALUES ('%s',' %s')''' % (word, 1))
            database.commit()
            cursor.close()
            database.close()
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        btn2 = types.KeyboardButton('✅Done')
        markup.add(btn2)
        bot.send_message(message.chat.id, 'Потвердитe', reply_markup=markup)
        bot.register_next_step_handler(message, news)
    else:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Вернуться в меню', callback_data='menu')
        markup.add(btn1)
        bot.send_message(message.chat.id, 'Ошибка ввода слова: Это не слово', reply_markup=markup)


def news(message):
    """

    :param message:
    :type
    :returns: None
    """
    global main_url
    print(type(message))
    main_url = requests.get(main_url).json()
    if main_url['totalResults'] == 0:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Вернуться в меню', callback_data='menu')
        markup.add(btn1)
        bot.send_message(message.chat.id, 'Нет артиклей по данному ключу', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Вернуться в меню', callback_data='menu'))

        article = main_url['articles']
        news_title = []
        news_url = []
        news_time = []
        counter = 0
        for art in article:
            news_title.append(art['title'])
            news_url.append(art['url'])
            news_time.append(art['publishedAt'])
            counter += 1
            if counter >= 5:
                break

            info = news_title[randint(0, counter-1)]
            bot.send_message(message.chat.id, f'{info}\n<a href=\"{news_url[news_title.index(info)]}\">'
                                              f'Подробнее о данной новости...</a>\n'
                                              f'{news_time[news_title.index(info)]}',
                             reply_markup=markup, parse_mode='html')
            return


bot.polling()
