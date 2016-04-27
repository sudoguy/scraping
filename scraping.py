import requests

main_url = "https://bibinet.ru/catalog/parts_mark_model/"
s = requests.Session()
s.get(main_url)


def load_parts_data(mark, model, page, session):
    url = '/'.join(main_url, mark, model, '?page=' + page)
    request = session.get(url)


with open('test.html', 'w') as output_file:
    output_file.write(r.text.encode('utf-8'))

marks = {}
