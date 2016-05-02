import os
import re
import requests
import shutil
import json
import psycopg2

from bs4 import BeautifulSoup

main_url = "https://bibinet.ru/catalog/parts_mark_model"

s = requests.Session()
s.get(main_url)

# Configuration block
#
# Выводить на экран запчасти
print_parts = True
# Количество используемых моделей в каждой марке
models_in_load = 2
# Количество страниц на каждую модель авто, с которых необходимо собрать информацию
pages_for_model = 3
# Имя БД, таблицы, пользователь и пароль, хост
db_name = 'scraping'
table_name = 'parts'
db_user = 'test_user'
db_user_password = 'qwerty'
db_host = 'localhost'


# Метод получения марок авто
def get_marks(session):
    print('---------------------')
    print('Получаем список марок')
    url = 'https://bibinet.ru/service/get_reference/?variants=mark'
    resp = session.get(url)
    marks_json = json.loads(resp.text)
    marks_list = []
    for mark in marks_json:
        marks_list.append((mark[0], mark[1]))
    print('---------------------')
    print('Марки получены (' + str(len(marks_list)) + ')')
    return marks_list


# Метод получения моделей для определенной марки авто
def get_models(session, mark_id):
    url = 'https://bibinet.ru/service/get_reference/?variants=model&mark=' + str(mark_id)
    resp = session.get(url)
    models_json = json.loads(resp.text)
    models_list = []
    for model in models_json:
        models_list.append(model[1])
    return models_list


# Получаем страницу с запчастями
def load_parts_data(mark, model, page, session):
    url = '/'.join((main_url, mark, model, '?page=' + str(page)))
    request = session.get(url)
    return request.text


# Проверка на то, есть ли на странице запчасти
def contain_parts_data(text):
    soup = BeautifulSoup(text, 'html.parser')
    parts_list = soup.find('tr', {'class': 'el'})
    return parts_list is not None


# Метод получения фото для определенной запчасти
def get_photo(link):
    link = str(link).replace('c80x0', 'c800x0')
    for x in range(10):
        r = requests.get(link, stream=True)
        if r.status_code == 200:
            filename = re.search(r'(?<=parts/).+', link).group()
            os.makedirs('photos/', exist_ok=True)
            with open('photos/' + filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            return os.path.abspath('photos/%s' % filename)
    else:
        return None


# Метод получения запчастей на странице для конкретной модели и марки
def get_parts_data(text, mark, model):
    soup = BeautifulSoup(text, 'html.parser')
    items = soup.find('div', {'id': 'fs_rezult'}).find_all('tr', {'class': 'el'})

    parts = []

    for item in items:
        soup = BeautifulSoup(str(item), 'html.parser')
        photo_unavailable = '/static/v3/img/photo-unavailable-01.png'
        if soup.find('td', {'class': 'photo'}).find('img')['src'] != photo_unavailable:
            part_photo = get_photo('https://' + soup.find('td', {'class': 'photo'}).find('img')['src'][2:])
        else:
            part_photo = None
        part_name = soup.find('td', {'class': 'part'}).find('a').text
        part_company = soup.find('td', {'class': 'company'}).find('a', {'class': 'link'}).text
        if soup.find('div', {'class': 'price'}).text == 'по запросу':
            part_price = None
        else:
            part_price = re.search(r'(\d| )+(?= руб)', soup.find('div', {'class': 'price'}).text).group().replace(" ",
                                                                                                                  "")
        parts_auto = str(soup.find('td', {'class': 'auto'}))
        parts_frame = re.search(r'(?<=<br/>[Кк]узов: )(\w|\(|\)| |\.)+', parts_auto)
        parts_year = re.search(r'(?<=<br/>[гГ]од выпуска: )\d{4}', parts_auto)
        parts_engine = re.search(r'(?<=<br/>[Дд]вигатель: )(\w|\(|\)| |\.)+', parts_auto)
        parts.append([
            part_name,  # Тип запчасти
            part_photo,  # Путь к фото
            part_company,  # Название компании
            parts_frame.group() if parts_frame else None,  # Тип кузова
            parts_year.group() if parts_year else parts_year,  # Год выпуска
            parts_engine.group() if parts_engine else parts_engine,  # Двигатель
            part_price,  # Стоимость
            str(mark).replace('_', ' '),  # Марка
            str(model).replace('_', ' '),  # Модель
        ])

    return parts


def show_part(part):
    print('+-------------------------------------+')
    print('Марка: ' + part[7])
    print('Модель: ' + part[8])
    print('Тип запчасти: ' + part[0])
    print('Компания: ' + part[2])
    print('Тип кузова: ' + str(part[3]))
    print('Фото: ' + str(part[1]))
    print('Год выпуска: ' + str(part[4]))
    print('Двигатель: ' + str(part[5]))
    print('Цена: ' + str(part[6]))


# Получение списка доступных марок авто
marks = get_marks(s)
marks_models = {}

print('---------------------')
print('Получаем список моделей')

for x in marks:
    marks_models[x[1]] = get_models(s, x[0])

print('---------------------')
print('Модели получены')

all_parts = []
# loading files
for mark in marks_models:
    models_loaded = 0
    for model in marks_models[mark]:
        if models_loaded < models_in_load:
            for page in range(1, pages_for_model + 1):
                data = load_parts_data(mark, model, page, s)
                if contain_parts_data(data):
                    if page == 1:
                        models_loaded += 1
                    parts_data = get_parts_data(data, mark, model)

                    for p in parts_data:
                        all_parts.append(p)
                        if print_parts:
                            show_part(p)
                else:
                    break
        else:
            break

# Подключаемся к БД
print('---------------------')
print('Подключаемся к БД')
conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % (db_host, db_name, db_user, db_user_password)
conn = psycopg2.connect(conn_string)

cur = conn.cursor()

for x in all_parts:
    cur.execute("""INSERT INTO parts
        (part_type, mark, model, frame, engine, year, price, company, photo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (x[0], x[7], x[8], x[3], x[5], x[4], float(x[6]) if x[6] else None, x[2], x[1]))
conn.commit()
conn.close()

print('---------------------')
print('Загрузка запчастей в БД завершена!')
