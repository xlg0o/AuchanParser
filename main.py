import requests
import fake_useragent
from bs4 import BeautifulSoup
from datetime import datetime
import json

headers = {
    "User-Agent": fake_useragent.UserAgent().random,
    'Accept-Language': 'uk-UA,uk;q=0.9',
}
link_sample = "https://auchan.zakaz.ua/uk/custom-categories/promotions/?page="

output_data = {}

# Получаем максимальное количество страниц
response = requests.get(link_sample, headers=headers)
soup = BeautifulSoup(response.text, "lxml")
max_page = int(soup.findAll('a', class_="Pagination__item")[-1].text)

# Один запрос для получения категорий
json_categories = 'https://stores-api.zakaz.ua/stores/48246401/categories/?only_parents=false'
categories_data_responce = requests.get(json_categories, headers=headers)
categories_data = categories_data_responce.json()


def find_titles_by_id(find_from, target_ids):
    titles = []
    stack = [find_from]

    while stack:
        current = stack.pop()

        # Проверяем, соответствует ли id целевому
        if isinstance(current, dict):
            if current.get("id") in target_ids:
                titles.append(current.get("title"))

            # Если есть дети, добавляем их в стек для дальнейшей обработки
            if "children" in current:
                stack.extend(current["children"])

        elif isinstance(current, list):
            stack.extend(current)

    return titles


def parse():
    for count in range(1, max_page + 1):
        print("-" * 15)
        print(f'NEW PAGE {count}')
        link = link_sample + str(count)
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")

        products_container = soup.find("div", attrs={"data-marker": "Products Box"})
        products = products_container.find_all("div", class_=lambda c: c and "ProductsBox__listItem" in c)

        for i in products:
            print("-" * 15)
            print('New element')

            product_link = "https://auchan.zakaz.ua" + i.find('a', class_='ProductTileLink')['href']
            product_id = i.find('a', class_='ProductTileLink')['href'].split('-')[-1].strip('/')

            # API ссылка для получения данных о продукте
            json_link = f'https://stores-api.zakaz.ua/stores/48246401/products/{product_id}/?include=recommended%2Csimilar%2Clinked&count=12'
            response = requests.get(json_link, headers=headers)
            data = response.json()

            # Обрабатываем полученные данные
            category_titles = find_titles_by_id(categories_data,
                                                [data['product']['parent_category_id'], data['product']['category_id']])

            temp_data = {
                "url_slug": data['product']['web_url'],
                "sku": data['product']['sku'],
                "title": data['product']['title'],
                "brand": data['product']['producer']['trademark'],
                "category": category_titles,
                "country": data['product']['country'],
                "price": data['product']['price'],
                "old_price": data['product']['discount']['old_price'],
                "discount_percentage": f"-{data['product']['discount']['value']}",
                "promotion_start": datetime.now().strftime("%Y-%m-%d"),
                "promotion_stop": data['product']['discount']['due_date'],
                "icon": data['product']['producer']['logo']['s64x64'],
                "ratio": data['product']['unit']
            }

            print(temp_data)
            output_data[product_id] = temp_data


# Запуск парсинга
try:
    parse()
except TypeError:
    with open('data.json', "w", encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)
    print("Данные успешно добавлены в файл.")
