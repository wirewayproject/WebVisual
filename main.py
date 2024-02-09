import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import gzip
from io import BytesIO
import mysql.connector

forbidden_words = ['github', 'cloudflare', 'tiktok', 'telegram', 'cdimage', 'ubuntu.com', 'twitter', 'x']  # Add your forbidden words here

forbidden_extensions = ['.exe', '.zip', '.rar', '.pdf', '.iso', '.tar', '.gz', '.jpg', '.png', '.zsync','.xz','.jpeg']  # Add your forbidden file extensions here

# MySQL database setup
conn = mysql.connector.connect(
    host='localhost',
    user='crawl',
    password='crawl',
    database='crawl'
)
cursor = conn.cursor()

# Create tables if they do not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS crawled_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        url VARCHAR(255) UNIQUE,
        title TEXT,
        description TEXT,
        content TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS link_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        url VARCHAR(255),
        link VARCHAR(255)
    )
''')
conn.commit()


async def fetch_url(session, url):
    async with session.get(url) as response:
        content_type = response.headers.get('content-type', '').lower()
        content_encoding = response.headers.get('content-encoding', '').lower()

        charset = 'utf-8'

        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].strip()

        try:
            if 'gzip' in content_encoding:
                content = await response.read()
                with gzip.GzipFile(fileobj=BytesIO(content)) as f:
                    html = f.read().decode(charset)
            else:
                html = await response.text(encoding=charset)
        except gzip.BadGzipFile:
            html = await response.text()
        except UnicodeDecodeError:
            print("found file")
            html = await response.text()

        return html


def extract_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()

    for a_tag in soup.find_all(['a', 'button'], href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        links.add(full_url)

        # Save to MySQL database
        save_link_to_db(base_url, full_url)

    return links


def extract_title_description_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else None

    meta_description_tag = soup.find('meta', {'name': 'description'})
    description = meta_description_tag['content'].strip() if meta_description_tag else None

    body_tag = soup.find('body')
    content = body_tag.text.strip() if body_tag else None

    return title, description, content


async def crawl_url(session, url, max_depth, stay_on_domain=True, current_depth=1, visited=set()):
    if (
        current_depth > max_depth
        or url in visited
        or (stay_on_domain and urlparse(url).netloc != urlparse(start_url).netloc)
        or not url.startswith(("http://", "https://"))
        or any(word in url for word in forbidden_words)
        or any(url.lower().endswith(extension) for extension in forbidden_extensions)
    ):
        return

    print(f"Crawling {url} (Depth {current_depth})")

    visited.add(url)
    try:
        html = await fetch_url(session, url)
        title, description, content = extract_title_description_content(html)
        save_to_db(url, title, description, content)

        links = await extract_links_concurrently(session, html, url, stay_on_domain)
    except Exception as e:
        print(f"Error crawling {url}: {str(e)}")
        return


    await asyncio.gather(*(crawl_url(session, link, max_depth, stay_on_domain, current_depth + 1, visited) for link in links))


async def extract_links_concurrently(session, html, base_url, stay_on_domain):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()

    async def fetch_link(url):
        full_url = urljoin(base_url, url)

        if stay_on_domain and urlparse(full_url).netloc != urlparse(start_url).netloc:
            return

        links.add(full_url)

        save_link_to_db(base_url, full_url)

    # Gather all the fetches concurrently
    await asyncio.gather(*(fetch_link(a_tag['href']) for a_tag in soup.find_all(['a', 'button'], href=True)))

    return links


def save_to_db(url, title, description, content):
    try:
        cursor.execute('INSERT INTO crawled_data (url, title, description, content) VALUES (%s, %s, %s, %s)',
                       (url, title, description, content))
        conn.commit()
        print(f"Saved {url} to the database")
    except mysql.connector.IntegrityError:
        print(f"URL {url} already exists in the database")


def save_link_to_db(base_url, link):
    try:
        cursor.execute('INSERT INTO link_data (url, link) VALUES (%s, %s)', (base_url, link))
        conn.commit()
    except mysql.connector.IntegrityError:
        print(f"Link {link} already exists in the database")


async def main(start_url, max_depth, stay_on_domain=True):
    async with aiohttp.ClientSession() as session:
        await crawl_url(session, start_url, max_depth, stay_on_domain)


if __name__ == "__main__":
    start_url = "https://vleer.app"  # Replace with your starting URL
    max_depth = 8  # Set the maximum depth for crawling
    stay_on_domain = False  # Set to False if you want to crawl across different domains

    asyncio.run(main(start_url, max_depth, stay_on_domain))


    conn.close()
