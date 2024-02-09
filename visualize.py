import asyncio
import mysql.connector
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse, urljoin
from tqdm import tqdm

forbidden_words = ['github', 'cloudflare', 'tiktok', 'telegram', 'cdimage', 'ubuntu.com', 'twitter', 'x']
forbidden_extensions = ['.exe', '.zip', '.rar', '.pdf', '.iso', '.tar', '.gz', '.jpg', '.png', '.zsync', '.xz', '.jpeg']

def get_links_from_db(domain, cursor):
    cursor.execute('SELECT DISTINCT link FROM link_data WHERE url LIKE %s', (f'%{domain}%',))
    return [link[0] for link in cursor.fetchall()]

def is_valid_domain(domain):
    return not any(word in domain for word in forbidden_words) and not domain.lower().endswith(tuple(forbidden_extensions))

async def crawl_domain(domain, graph, cursor, depth=1, max_depth=3):
    if depth > max_depth or not is_valid_domain(domain):
        return

    tqdm.write(f"Crawling {domain} (Depth {depth})")

    try:
        links = get_links_from_db(domain, cursor)

        for link in tqdm(links, desc='Processing Links', leave=False):
            parsed_url = urlparse(link)
            base_domain = parsed_url.netloc
            graph.add_edge(domain, base_domain)

            if is_valid_domain(base_domain):
                if base_domain not in graph.nodes:
                    graph.add_node(base_domain)

                await crawl_domain(base_domain, graph, cursor, depth + 1, max_depth)

    except Exception as e:
        tqdm.write(f"Error crawling {domain}: {str(e)}")

async def main(start_url, max_depth):
    graph = nx.DiGraph()

    conn = mysql.connector.connect(
        host='localhost',
        user='crawl',
        password='crawl',
        database='crawl'
    )
    cursor = conn.cursor()

    start_domain = urlparse(start_url).netloc
    graph.add_node(start_domain)

    await crawl_domain(start_domain, graph, cursor, max_depth=max_depth)

    cursor.close()
    conn.close()

    pos = nx.spring_layout(graph)
    
    # Adjust figure size based on the number of nodes
    plt.figure(figsize=(len(graph.nodes) * 0.4, len(graph.nodes) * 0.4))
    
    nx.draw(graph, pos, with_labels=True, font_weight='bold', node_size=700, node_color='skyblue', arrowsize=20, connectionstyle='arc3,rad=0.1')
    
    # Save the figure with a high resolution (adjust dpi as needed)
    plt.savefig('graph_image2.png', dpi=300)
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    start_url = "https://vleer.app"  # Replace with your starting URL
    max_depth = 2  # Set the maximum depth for lookups

    asyncio.run(main(start_url, max_depth))
