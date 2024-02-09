import mysql.connector
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from datetime import datetime, timedelta

def calculate_changefreq(lastmod):
    # You can customize the logic to calculate changefreq based on lastmod
    return 'daily'

def generate_sitemap_xml(output_file='sitemap.xml'):
    conn = mysql.connector.connect(
        host='localhost',
        user='crawl',
        password='crawl',
        database='crawl'
    )

    cursor = conn.cursor()

    try:
        cursor.execute('SELECT url FROM crawled_data')
        urls_data = cursor.fetchall()

        root = Element('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})

        for url_data in urls_data:
            url_element = SubElement(root, 'url')

            loc_element = SubElement(url_element, 'loc')
            loc_element.text = url_data[0]

            lastmod_element = SubElement(url_element, 'lastmod')
            lastmod_element.text = (datetime.utcnow() - timedelta(hours=1)).isoformat()

            changefreq_element = SubElement(url_element, 'changefreq')
            changefreq_element.text = calculate_changefreq(lastmod_element.text)

        tree = ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

        print(f"Sitemap XML generated and saved to {output_file}")

    except mysql.connector.Error as e:
        print(f"Error generating sitemap XML from the database: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    generate_sitemap_xml()
