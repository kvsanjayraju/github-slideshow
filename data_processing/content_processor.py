import spacy
from bs4 import BeautifulSoup
import re

# --- spaCy Model Setup ---
# Make sure to download the spaCy model before running the script for the first time.
# You can download it by running the following command in your terminal:
# python -m spacy download en_core_web_sm
# Or, uncomment and run the following lines once:
# import subprocess
# subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model 'en_core_web_sm' not found.")
    print("Please download it by running: python -m spacy download en_core_web_sm")
    nlp = None # Set nlp to None if model loading fails

# --- Mock data for testing if news_fetcher.py is unavailable ---
MOCK_NEWS_ITEMS = [
    {
        "title": "Exciting Tech Conference Announced!",
        "link": "http://example.com/tech-conference",
        "published": "2024-07-30T10:00:00Z",
        "summary": "<p>Join us for the <b>annual Tech Summit</b> where industry leaders like Sundar Pichai from Google will discuss advancements in AI. Event in New Delhi.</p>\n\nExtra spaces here.",
    },
    {
        "title": "New Government Policy on Renewable Energy",
        "link": "http://example.com/renewable-policy",
        "published": "2024-07-29T14:30:00Z",
        "summary": "The Government of India launched a new policy to boost solar power. This initiative aims to reduce carbon emissions by 2030. The policy was announced by Shri R. K. Singh.",
    }
]

def process_articles(news_items: list) -> list:
    """
    Processes a list of news articles to clean text, segment sentences,
    extract named entities, and identify keywords.

    Args:
        news_items (list): A list of dictionaries, where each dictionary
                           represents a news item (from news_fetcher.py).

    Returns:
        list: The list of news_items, updated with processed information.
    """
    if nlp is None:
        print("spaCy model not loaded. Cannot process articles.")
        # Return items with a note about processing failure
        for item in news_items:
            item["processing_status"] = "Failed: spaCy model not available"
        return news_items

    processed_items = []
    for item in news_items:
        if "summary" not in item or not item["summary"]:
            print(f"Skipping item due to missing or empty summary: {item.get('title', 'N/A')}")
            item.update({
                "cleaned_text": "",
                "sentences": [],
                "named_entities": [],
                "keywords": [],
                "processing_status": "Skipped: No summary"
            })
            processed_items.append(item)
            continue

        summary = item["summary"]

        # 1. Text Cleaning
        # Remove HTML tags
        soup = BeautifulSoup(summary, "html.parser")
        cleaned_text = soup.get_text()

        # Normalize whitespace (remove extra spaces, newlines, tabs)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        item["cleaned_text"] = cleaned_text

        # 2. spaCy Processing
        doc = nlp(cleaned_text)

        # Sentence Segmentation
        item["sentences"] = [sent.text for sent in doc.sents]

        # Named Entity Recognition (NER)
        entities = []
        for ent in doc.ents:
            entities.append((ent.text, ent.label_))
        item["named_entities"] = entities

        # Basic Keyword Extraction (using noun chunks)
        # Noun chunks are base noun phrases (e.g., "autonomous cars", "AI applications")
        # This provides more meaningful keywords than just single nouns in many cases.
        keywords = list(set(chunk.text for chunk in doc.noun_chunks)) # Using set to avoid duplicates
        item["keywords"] = keywords
        
        item["processing_status"] = "Successfully processed"
        processed_items.append(item)

    return processed_items

if __name__ == "__main__":
    print("Starting content processing demo...")

    # Attempt to load actual news items
    sample_articles = []
    try:
        # Assuming news_fetcher.py is in the same directory or accessible in PYTHONPATH
        from news_fetcher import fetch_news_from_feeds 
        print("Fetching live news items using news_fetcher...")
        sample_articles = fetch_news_from_feeds()
        if not sample_articles:
            print("No articles fetched by news_fetcher. Using mock data.")
            sample_articles = MOCK_NEWS_ITEMS
    except ImportError:
        print("news_fetcher.py not found. Using mock data for demonstration.")
        sample_articles = MOCK_NEWS_ITEMS
    except Exception as e:
        print(f"Error fetching live news: {e}. Using mock data.")
        sample_articles = MOCK_NEWS_ITEMS


    if not sample_articles:
        print("No data (live or mock) available to process. Exiting.")
    else:
        print(f"\nProcessing {len(sample_articles)} articles...")
        processed_articles = process_articles(sample_articles)

        if processed_articles:
            print("\n--- Sample Processed Article ---")
            article_to_display = processed_articles[0] # Display the first article
            
            print(f"Title: {article_to_display.get('title', 'N/A')}")
            print(f"Cleaned Text: {article_to_display.get('cleaned_text', 'N/A')}")
            
            print("\nSentences:")
            for i, sentence in enumerate(article_to_display.get('sentences', [])):
                print(f"  {i+1}. {sentence}")
            
            print("\nNamed Entities:")
            for entity_text, entity_label in article_to_display.get('named_entities', []):
                print(f"  - {entity_text} ({entity_label})")
            
            print("\nKeywords:")
            for i, keyword in enumerate(article_to_display.get('keywords', [])):
                print(f"  - {keyword}")
            print(f"\nProcessing Status: {article_to_display.get('processing_status', 'N/A')}")
        else:
            print("\nNo articles were processed.")
    
    print("\nContent processing demo finished.")
