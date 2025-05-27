import unittest
from unittest.mock import patch, MagicMock
from data_processing.news_fetcher import fetch_news_from_feeds, RSS_FEED_URLS
import feedparser
import requests

# Sample RSS feed XML content for mocking
SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>Sample Feed</title>
    <item>
        <title>Sample Title 1</title>
        <link>http://example.com/article1</link>
        <published>Tue, 30 Jul 2024 10:00:00 +0000</published>
        <summary>This is the summary for article 1.</summary>
    </item>
    <item>
        <title>Sample Title 2</title>
        <link>http://example.com/article2</link>
        <updated>Tue, 30 Jul 2024 11:00:00 +0000</updated>
        <description>This is the description for article 2.</description>
    </item>
</channel>
</rss>"""

# Another sample for a different feed URL if needed, or to test multiple calls
SAMPLE_RSS_XML_2 = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>Sample Feed 2</title>
    <item>
        <title>Sample Title 3</title>
        <link>http://example.com/article3</link>
        <published>Wed, 31 Jul 2024 12:00:00 +0000</published>
        <summary>Summary for article 3.</summary>
    </item>
</channel>
</rss>"""


class TestNewsFetcher(unittest.TestCase):

    @patch('data_processing.news_fetcher.requests.get')
    def test_fetch_news_from_feeds_success(self, mock_get):
        # Configure the mock response for requests.get
        # We need to mock for each URL in RSS_FEED_URLS
        
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.content = SAMPLE_RSS_XML.encode('utf-8')
        mock_response_1.raise_for_status = MagicMock()

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.content = SAMPLE_RSS_XML_2.encode('utf-8')
        mock_response_2.raise_for_status = MagicMock()
        
        # Set up the side_effect for multiple calls if there are multiple feed URLs
        if len(RSS_FEED_URLS) > 1:
            mock_get.side_effect = [mock_response_1, mock_response_2] + [MagicMock(status_code=200, content="<rss><channel></channel></rss>".encode('utf-8'))]*(len(RSS_FEED_URLS)-2)
        elif RSS_FEED_URLS: # handles if there's only one URL
             mock_get.return_value = mock_response_1
        else: # No URLs, should return empty
            mock_get.return_value = MagicMock(status_code=200, content="<rss><channel></channel></rss>".encode('utf-8'))


        news_items = fetch_news_from_feeds()

        # Assertions
        self.assertIsInstance(news_items, list)
        
        expected_total_items = 0
        if RSS_FEED_URLS: # Only expect items if URLs are defined
            if len(RSS_FEED_URLS) >= 1: expected_total_items += 2 # From SAMPLE_RSS_XML
            if len(RSS_FEED_URLS) >= 2: expected_total_items += 1 # From SAMPLE_RSS_XML_2
        
        self.assertEqual(len(news_items), expected_total_items)

        if expected_total_items > 0:
            # Check first item (from SAMPLE_RSS_XML)
            item1 = next((item for item in news_items if item["title"] == "Sample Title 1"), None)
            self.assertIsNotNone(item1)
            self.assertEqual(item1["link"], "http://example.com/article1")
            self.assertEqual(item1["published"], "Tue, 30 Jul 2024 10:00:00 +0000")
            self.assertEqual(item1["summary"], "This is the summary for article 1.")

            # Check second item (from SAMPLE_RSS_XML)
            item2 = next((item for item in news_items if item["title"] == "Sample Title 2"), None)
            self.assertIsNotNone(item2)
            self.assertEqual(item2["link"], "http://example.com/article2")
            # feedparser uses 'updated' if 'published' is not present for the 'published' key in its dict
            self.assertEqual(item2["published"], "Tue, 30 Jul 2024 11:00:00 +0000") 
            self.assertEqual(item2["summary"], "This is the description for article 2.")

        if expected_total_items > 2: # If SAMPLE_RSS_XML_2 was used
            item3 = next((item for item in news_items if item["title"] == "Sample Title 3"), None)
            self.assertIsNotNone(item3)
            self.assertEqual(item3["link"], "http://example.com/article3")
            self.assertEqual(item3["published"], "Wed, 31 Jul 2024 12:00:00 +0000")
            self.assertEqual(item3["summary"], "Summary for article 3.")


    @patch('data_processing.news_fetcher.requests.get')
    def test_fetch_news_from_feeds_request_exception(self, mock_get):
        # Configure mock_get to raise a RequestException for all feed URLs
        mock_get.side_effect = requests.exceptions.RequestException("Test network error")

        news_items = fetch_news_from_feeds()

        self.assertEqual(len(news_items), 0) # Should return an empty list

    @patch('data_processing.news_fetcher.requests.get')
    def test_fetch_news_from_feeds_http_error(self, mock_get):
        # Configure mock_get to return an HTTP error status code
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_get.return_value = mock_response
        
        news_items = fetch_news_from_feeds()
        self.assertEqual(len(news_items), 0) # Should return an empty list

    @patch('data_processing.news_fetcher.requests.get')
    def test_fetch_news_from_feeds_empty_feed(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = "<rss version='2.0'><channel><title>Empty Feed</title></channel></rss>".encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        news_items = fetch_news_from_feeds()
        self.assertEqual(len(news_items), 0)
    
    def test_fetch_news_with_no_urls_defined(self):
        # Temporarily modify RSS_FEED_URLS for this test
        original_urls = list(RSS_FEED_URLS) # Make a copy
        RSS_FEED_URLS.clear() # Empty the list

        news_items = fetch_news_from_feeds()
        self.assertEqual(len(news_items), 0)

        # Restore original URLs
        RSS_FEED_URLS.extend(original_urls)


if __name__ == '__main__':
    unittest.main()
