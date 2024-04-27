import asyncio
import sqlite3
from playwright.async_api import async_playwright

SITE_URL = 'https://naked-science.ru/article'
PAGE_URL = lambda page_number: f'{SITE_URL}/page/{page_number}'

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

# Основная функция для сохранения данных в базе данных SQLite
def save_to_database(title, body):
    conn = sqlite3.connect('articles.db')
    create_table(conn)
    insert_article(conn, title, body)
    # TODO: добавить сохранение связанных комментариев (если есть)
    conn.close()

async def get_page_urls(page):
    page_urls = []
    await page.goto(SITE_URL)
    pagination = await page.query_selector('.pagination-block')
    pagination = await pagination.query_selector_all('.page-numbers')
    pages = [await item.inner_text() for item in pagination]
    pages = [page.strip().replace('\xa0', '') for page in pages]
    page_numbers = []
    for page in pages:
        try:
            page_numbers.append(int(page))
        except Exception:
            continue

    min_page = min(page_numbers)
    max_page = max(page_numbers)
    page_urls.extend([PAGE_URL(page_number) for page_number in range(min_page, max_page + 1)])
    return page_urls

async def get_article_urls(page_url, page):
    await page.goto(page_url)
    article_urls = []
    urls = await page.query_selector_all('.news-item .news-item-title a')

    for item in urls:
        href = await item.get_attribute('href')
        article_urls.append(href)

    return article_urls

async def get_article_content(article_url, page):
    await page.goto(article_url)

    title_object = await page.query_selector('h1')
    title = await title_object.inner_text()

    body = await page.query_selector('.body')
    article = await body.query_selector_all('p')
    
    body = [await item.inner_text() for item in article]

    return title, body

async def main():
    conn = sqlite3.connect('articles.db')
    create_table(conn)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        page_urls = await get_page_urls(page)
        for page_url in page_urls:
            article_urls = await get_article_urls(page_url, page)
            for article_url in article_urls:
                title, body = await get_article_content(article_url, page)
                if title and body:
                    save_to_database(title, body)
    
        # Добавляем асинхронное ожидание перед закрытием браузера
        await asyncio.sleep(5)
        await browser.close()

    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
