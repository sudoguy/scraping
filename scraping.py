from pprint import pprint

import requests, re
from bs4 import BeautifulSoup

main_url = "https://bibinet.ru/catalog/parts_mark_model"

s = requests.Session()
s.get(main_url)


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


def load_parts_data(mark, model, page, session):
    url = '/'.join((main_url, mark, model, '?page=' + str(page)))
    request = session.get(url)
    return request.text


def contain_parts_data(text):
    soup = BeautifulSoup(text)
    parts_list = soup.find('tr', {'class': 'el'})
    print(parts_list)
    return parts_list is not None


marks = get_marks(s)
qwer = r''
# print(marks)
marks_models = {}
for x in marks:
    marks_models[x] = get_models(s, x)

pprint(marks_models)

# loading files
# page = 1
# for x in range(3):
#     data = load_parts_data(mark, model, page, s)
#     if contain_parts_data(data):
#         with open('./%s_%s_page_%d.html' % (mark, model, page), 'w') as output_file:
#             output_file.write(data)
#             page += 1
#     else:
#         break
