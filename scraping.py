import os
import re
import requests
import shutil
from bs4 import BeautifulSoup

main_url = "https://bibinet.ru/catalog/parts_mark_model"

s = requests.Session()
s.get(main_url)


# todo: Получение списка марок
# https://bibinet.ru/service/get_reference/?variants=mark

# todo: Получение списка моделей
# https://bibinet.ru/service/get_reference/?variants=model&mark=4

def get_marks(session):
    request = session.get(main_url)
    soup = BeautifulSoup(request.text, 'html.parser')
    marks_list = []
    marks = soup.find('div', {'class': 'catalog_list_punkt'}).find_all('a', {'class': 'el'})
    for mark in marks:
        marks_list.append(str(mark.text).replace(' ', '_'))
    return marks_list


def get_models(session, mark):
    while True:
        request = session.get('/'.join((main_url, mark)))
        if request.status_code == 200:
            soup = BeautifulSoup(request.text, 'html.parser')
            models_list = []
            models = soup.find('div', {'class': 'catalog_list_punkt'}).find('div', {'class': 'sub'}).find_all('a', {
                'class': 'el'})
            for model in models:
                regex_result = re.search(r'(?<=%s ).+' % str(mark).replace('_', ' '), model.text)
                models_list.append(regex_result.group().replace(' ', '_'))
            return models_list


# Получаем страницу с запчастями
def load_parts_data(mark, model, page, session):
    url = '/'.join((main_url, mark, model, '?page=' + str(page)))
    request = session.get(url)
    return request.text


def contain_parts_data(text):
    soup = BeautifulSoup(text, 'html.parser')
    parts_list = soup.find('tr', {'class': 'el'})
    return parts_list is not None


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


marks = get_marks(s)
marks_models = {}
for x in marks:
    marks_models[x] = get_models(s, x)

# loading files
for mark in marks_models:
    for model in marks_models[mark]:
        for page in range(1, 2):
            data = load_parts_data(mark, model, page, s)
            if contain_parts_data(data):
                parts_data = get_parts_data(data, mark, model)
                for part in parts_data:
                    print('+-------------------------------------+')
                    print('Марка: ' + part[7])
                    print('Модель: ' + part[8])
                    print('Тип запчасти: ' + part[0])
                    print('Компания: ' + part[2])
                    print('Тип кузова: ' + str(part[3]))
                    print('Фото: ' + str(part[1]))
                    print('Год выпуска: ' + str(part[4]))
                    print('Двигатель: ' + str(part[5]))
                    print('Цена: ' + part[6])
            else:
                break
