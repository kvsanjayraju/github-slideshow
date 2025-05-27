import feedparser
import requests

RSS_FEED_URLS = [
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",  # PIB All Releases
    "https://prasarbharati.gov.in/feed/",  # Prasar Bharati
]

def fetch_news_from_feeds():
    """
    Fetches news items from a list of RSS feeds.

    Returns:
        list: A list of dictionaries, where each dictionary represents a news item.
              Returns an empty list if fetching fails for all feeds.
    """
    news_items = []
    for url in RSS_FEED_URLS:
        try:
            print(f"Fetching news from: {url}")
            # Using requests to get the feed content with a timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Parsing the feed content using feedparser
            feed = feedparser.parse(response.content)

            for entry in feed.entries:
                news_item = {
                    "title": entry.get("title", "N/A"),
                    "link": entry.get("link", "N/A"),
                    "published": entry.get("published", entry.get("updated", "N/A")),
                    "summary": entry.get("summary", entry.get("description", "N/A")),
                }
                news_items.append(news_item)
            print(f"Fetched {len(feed.entries)} items from {url}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching feed from {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {url}: {e}")
            
    return news_items

if __name__ == "__main__":
    print("Starting news fetching process...")
    all_news = fetch_news_from_feeds()

    if all_news:
        print(f"\nSuccessfully fetched a total of {len(all_news)} news items.")
        print("\nSample of the first news item fetched:")
        for key, value in all_news[0].items():
            print(f"  {key.capitalize()}: {value}")
    else:
        print("\nNo news items fetched. Please check the RSS feed URLs and network connectivity.")

    print("\nFinal RSS Feed URLs used:")
    for url in RSS_FEED_URLS:
        print(f"- {url}")
