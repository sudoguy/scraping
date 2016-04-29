from pprint import pprint

import re
import requests
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
    soup = BeautifulSoup(request.text)
    marks_list = []
    marks = soup.find('div', {'class': 'catalog_list_punkt'}).find_all('a', {'class': 'el'})
    for mark in marks:
        marks_list.append(str(mark.text).replace(' ', '_'))
    return marks_list


def get_models(session, mark):
    while True:
        request = session.get('/'.join((main_url, mark)))
        if request.status_code == 200:
            soup = BeautifulSoup(request.text)
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
    soup = BeautifulSoup(text)
    parts_list = soup.find('tr', {'class': 'el'})
    return parts_list is not None


def get_parts_data(text):
    soup = BeautifulSoup(text)
    items = soup.find('div', {'id': 'fs_rezult'}).find_all('tr', {'class': 'el'})

    parts = []

    for item in items:
        soup = BeautifulSoup(str(item))
        part_photo = None
        part_name = soup.find('td', {'class': 'part'}).find('a').text
        part_company = soup.find('td', {'class': 'company'}).find('a', {'class': 'link'}).text
        tex = soup.find('div', {'class': 'price'}).text
        if soup.find('div', {'class': 'price'}).text == 'по запросу':
            part_price = 'цена по запросу'
        else:
            part_price = re.search(r'(\w| )+(?= руб)', soup.find('div', {'class': 'price'}).text).group().replace(' ',
                                                                                                                  '')
        parts.append([part_name, part_photo, part_company, part_price])

    print(parts)
    return parts

marks = get_marks(s)
marks_models = {}
for x in marks:
    marks_models[x] = get_models(s, x)

# pprint(marks_models)

# loading files
for mark in marks_models:
    for model in marks_models[mark]:
        for page in range(1, 4):
            data = load_parts_data(mark, model, page, s)
            if contain_parts_data(data):
                get_parts_data(data)
            else:
                break
