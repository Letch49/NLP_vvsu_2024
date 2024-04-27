from bs4 import BeautifulSoup
import requests
import sqlite3

SITE_URL = 'https://naked-science.ru/article'
PAGE_URL = lambda page_number : f'{SITE_URL}/page/{page_number}'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

# Функция для создания таблицы в базе данных SQLite
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS articles
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT,
                          body TEXT)''')
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при создании таблицы:", e)

# Функция для добавления записи в базу данных SQLite
def insert_article(conn, title, body):
    try:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO articles (title, body) VALUES (?, ?)''', (title, "\n".join(body)))
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при добавлении записи:", e)

# Основная функция для сохранения данных в базу данных SQLite
def save_to_database(title, body):
    conn = sqlite3.connect('articles.db')
    create_table(conn)
    insert_article(conn, title, body)
    # TODO: добавить сохранение связанных коментариев (если есть)
    conn.close()

def get_page_urls(site_url):
    response = requests.get(site_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
        pagination = soup.find(class_='pagination-block')
        cleaned_text = pagination.text.strip()
        pages = cleaned_text.replace('\xa0', '').split('\n')
        pages = [int(page) for page in pages if page != '…']
        min_page = min(pages)
        max_page = max(pages)
        return [PAGE_URL(page_number) for page_number in range(min_page, max_page+1)]
    else:
        print('Ошибка при запросе:', response.status_code)
        return []

def get_article_urls(page_url):
    response = requests.get(page_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find_all(class_='news-item')
        return [item.find('a').get('href') for item in content]
    else:
        print('Ошибка при запросе:', response.status_code)
        return []

def get_article_content(article_url):
    response = requests.get(article_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
        # TODO: реализовать очистку текста
        # TODO: добавить сохранение коментов
        title = soup.find('h1').text
        body = soup.find('body').find_all('p')
        body = [_.text for _ in body]
        return title, body
    else:
        print('Ошибка при запросе:', response.status_code)
        return None, None

def main():
    site_url = 'https://naked-science.ru/article'
    page_urls = get_page_urls(site_url) # получаем страницы сайта
    for page_url in page_urls:
        article_urls = get_article_urls(page_url) # получаем адреса статей на странице
        for article_url in article_urls:
            title, body = get_article_content(article_url) # получаем содержание статьи
            if title and body:
                # TODO: необходимо реализовать проверку существования записи в БД (например обеспечить уникальность по URL)
                save_to_database(title, body)

if __name__ == "__main__":
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }
    main()
