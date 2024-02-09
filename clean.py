import os
import mysql.connector

def clean_database():
    conn = mysql.connector.connect(
        host='localhost',
        user='crawl',
        password='crawl',
        database='crawl'
    )

    cursor = conn.cursor()

    try:
        cursor.execute('DROP TABLE IF EXISTS crawled_data')
        cursor.execute('DROP TABLE IF EXISTS link_data')
        conn.commit()

        print("Database cleaned successfully")

    except mysql.connector.Error as e:
        print(f"Error cleaning the database: {e}")

    finally:
        conn.close()

def clean_sitemap_file():
    try:
        os.remove('sitemap.xml')
        print("Sitemap file removed successfully")

    except OSError as e:
        print(f"Error removing sitemap file: {e}")

if __name__ == "__main__":
    clean_database()
    clean_sitemap_file()
