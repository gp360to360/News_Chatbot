import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from qdrant_client import QdrantClient, models
import uuid
import os
import time # Import time for a small delay
from dotenv import load_dotenv; 
load_dotenv()

# --- 1. CONFIGURATION ---
# IMPORTANT: Replace with your actual Jina API Key
JINA_API_KEY = os.getenv("JINA_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")    
QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME") 

# --- 2. FUNCTION TO GET ARTICLE URLS FROM SITEMAP ---
def get_article_urls(sitemap_index_url, limit=50):
    """
    Fetches a sitemap index, finds the first news sitemap, and then extracts article URLs from it.
    """
    urls = []
    print(f"Fetching sitemap index from: {sitemap_index_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        # Step 1: Fetch and parse the sitemap index
        index_response = requests.get(sitemap_index_url, headers=headers)
        index_response.raise_for_status()
        index_root = ET.fromstring(index_response.content)
        namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        news_sitemap_url = None
        
        # UPDATED: Based on the sitemap structure, we now simply take the FIRST sitemap URL.
        # The previous logic looking for "news.xml" was failing because no such URL exists in the index.
        print("Searching for the first available sitemap in the index...")
        first_sitemap_loc = index_root.find('sitemap:sitemap/sitemap:loc', namespace)

        if first_sitemap_loc is not None and first_sitemap_loc.text:
            news_sitemap_url = first_sitemap_loc.text
            print(f"Found sitemap to process: {news_sitemap_url}")
        else:
            print("Could not find any sitemap URL in the index. Please check the sitemap structure.")
            return []

        # Step 2: Fetch and parse the actual news sitemap
        print("Fetching articles from the news sitemap...")
        time.sleep(1) # Be polite and wait a second before the next request
        sitemap_response = requests.get(news_sitemap_url, headers=headers)
        sitemap_response.raise_for_status()
        sitemap_root = ET.fromstring(sitemap_response.content)

        for url_element in sitemap_root.findall('sitemap:url/sitemap:loc', namespace):
            urls.append(url_element.text)
            if len(urls) >= limit:
                break

    except requests.exceptions.RequestException as e:
        print(f"Error fetching or parsing sitemaps: {e}")
    
    print(f"Found {len(urls)} article URLs.")
    return urls

# --- 3. FUNCTION TO SCRAPE AND CHUNK ARTICLE CONTENT ---
def scrape_and_chunk(url):
    """Scrapes the text from a URL and splits it into paragraph chunks."""
    print(f"Scraping: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # REVERTED: Switched selector back to the one for Reuters articles.
        # It uses a data-testid attribute which is generally more stable than class names.
        article_body = soup.find('div', attrs={'data-testid': 'ArticleBody'})
        
        if article_body:
            paragraphs = article_body.find_all('p')
        else:
            # If the main body isn't found, return an empty list to avoid errors.
            paragraphs = []
        
        # Chunking by paragraph, filtering out short/irrelevant ones
        chunks = [p.get_text() for p in paragraphs if len(p.get_text().split()) > 25]
        return chunks
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# --- 4. FUNCTION TO GENERATE EMBEDDINGS ---
def get_embeddings(texts, api_key):
    """Gets embeddings for a list of texts using the Jina API."""
    if not api_key or "your_jina_api_key" in api_key:
        raise ValueError("JINA_API_KEY is not set. Please add your key to the script.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.post(
        "https://api.jina.ai/v1/embeddings",
        headers=headers,
        json={"input": texts, "model": "jina-embeddings-v2-base-en"},
    )
    response.raise_for_status()
    embeddings = [res["embedding"] for res in response.json()["data"]]
    return embeddings

# --- 5. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    print("🚀 Starting RAG Pipeline Ingestion...")
    
    # Initialize the Qdrant client
    qdrant_client = QdrantClient(url=QDRANT_URL,api_key = QDRANT_API_KEY)
    
    # UPDATED: Address the DeprecationWarning by using the new recommended methods.
    # First, check if the collection exists and delete it to ensure a fresh start.
    if qdrant_client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' already exists. Deleting it.")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' deleted.")

    # Now, create the new collection.
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=768,  # Jina v2 base embeddings are 768 dimensions
            distance=models.Distance.COSINE
        ),
    )
    print(f"Qdrant collection '{COLLECTION_NAME}' created successfully.")

    # UPDATED: Using the Reuters sitemap index URL provided.
    reuters_sitemap_index_url = "https://www.reuters.com/arc/outboundfeeds/sitemap-index/?outputType=xml"
    article_urls = get_article_urls(reuters_sitemap_index_url, limit=50)
    
    all_chunks = []
    for url in article_urls:
        chunks = scrape_and_chunk(url)
        if chunks:
            all_chunks.extend(chunks)

    print(f"\nTotal text chunks to process: {len(all_chunks)}")

    # Process chunks in batches to be memory-efficient and avoid API rate limits
    batch_size = 32 
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}...")
        
        # 1. Get embeddings for the current batch
        batch_embeddings = get_embeddings(batch_chunks, JINA_API_KEY)
        
        # 2. Prepare points for Qdrant
        points_to_upsert = [
            models.PointStruct(
                id=str(uuid.uuid4()),  # Generate a unique ID for each chunk
                vector=embedding,
                payload={"text": chunk}  # Store the original text with its vector
            )
            for chunk, embedding in zip(batch_chunks, batch_embeddings)
        ]

        # 3. Upsert (upload) the points to the Qdrant collection
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_upsert,
            wait=True,  # Wait for the operation to complete
        )

    print("\n✅ RAG pipeline ingestion complete!")
    print(f"All news chunks have been embedded and stored in the '{COLLECTION_NAME}' collection in Qdrant.")

