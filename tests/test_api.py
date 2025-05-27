import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# --- Add parent directory to sys.path for module imports ---
# This ensures that 'api.app' and its subsequent imports can be found
# current_dir = os.path.dirname(os.path.abspath(__file__)) # tests directory
# project_root = os.path.dirname(current_dir) # project root
# if project_root not in sys.path:
#    sys.path.insert(0, project_root)
# This path adjustment is now handled by tests/__init__.py

# --- Import the Flask app ---
# It's important that this import happens *after* sys.path is potentially modified
# if this file were to be run standalone without `python -m unittest discover`.
# However, with `tests/__init__.py`, this should work correctly.
from api.app import app as flask_app

# --- Mock data for API tests ---
MOCK_RAW_ARTICLES = [
    {"title": "API Test Article 1", "summary": "Content for article 1 for API test."}
]
MOCK_PROCESSED_ARTICLES = [
    {
        "title": "API Test Article 1", 
        "summary": "Content for article 1 for API test.",
        "cleaned_text": "Content for article 1 for API test.",
        "sentences": ["Content for article 1 for API test."],
        "named_entities": [("API", "ORG")], # Sample entity
        "keywords": ["Content", "API test"],
        "processing_status": "Successfully processed"
    }
]
MOCK_MCQS = [
    {
        "question": "What is API?",
        "options": ["API", "Another Thing", "Yet Another", "Final Option"],
        "correct_answer_text": "API",
        "source_article_title": "API Test Article 1",
        "source_article_link": "http://example.com/api-test-1"
    }
]

class TestApi(unittest.TestCase):

    def setUp(self):
        """Set up test client and other test variables."""
        flask_app.config['TESTING'] = True
        self.client = flask_app.test_client()
        # Ensure the spaCy model (even if mocked) is considered "loaded" by the API
        # The API checks `spacy_nlp` from `content_processor`
        # We can patch this check within the API's context if needed, or ensure
        # the actual content_processor.nlp is not None (if tests run after model download)
        
        # Forcing content_processor.nlp to not be None for API tests if it was None
        # This is a bit of a workaround for the API's direct check.
        # A better way might be to mock the spacy_nlp object within the api.app module directly.
        if 'data_processing.content_processor' in sys.modules:
            if sys.modules['data_processing.content_processor'].nlp is None:
                # If the model wasn't loaded, mock it for API tests to pass the check
                sys.modules['data_processing.content_processor'].nlp = MagicMock()


    @patch('api.app.fetch_news_from_feeds')
    @patch('api.app.process_articles')
    @patch('api.app.generate_mcqs_from_articles')
    def test_get_latest_mcqs_success(self, mock_generate_mcqs, mock_process_articles, mock_fetch_news):
        # Configure mocks to return successful data
        mock_fetch_news.return_value = MOCK_RAW_ARTICLES
        mock_process_articles.return_value = MOCK_PROCESSED_ARTICLES
        mock_generate_mcqs.return_value = MOCK_MCQS

        response = self.client.get('/api/mcqs/latest')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        
        self.assertEqual(data['message'], "MCQs generated successfully")
        self.assertEqual(data['mcqs'], MOCK_MCQS)
        
        mock_fetch_news.assert_called_once()
        mock_process_articles.assert_called_once_with(MOCK_RAW_ARTICLES)
        mock_generate_mcqs.assert_called_once_with(MOCK_PROCESSED_ARTICLES)

    @patch('api.app.fetch_news_from_feeds')
    def test_get_latest_mcqs_fetch_fails(self, mock_fetch_news):
        mock_fetch_news.return_value = [] # Simulate no articles fetched

        response = self.client.get('/api/mcqs/latest')
        
        self.assertEqual(response.status_code, 500) # As per current api.app error handling
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn("Could not fetch any news articles", data.get("error", ""))

    @patch('api.app.fetch_news_from_feeds')
    @patch('api.app.process_articles')
    def test_get_latest_mcqs_processing_fails(self, mock_process_articles, mock_fetch_news):
        mock_fetch_news.return_value = MOCK_RAW_ARTICLES
        # Simulate processing returning empty or unsuccessfully processed articles
        mock_process_articles.return_value = [{"processing_status": "Failed"}] 

        response = self.client.get('/api/mcqs/latest')
        
        self.assertEqual(response.status_code, 500) # As per current api.app error handling
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn("Failed to process the fetched articles", data.get("error", ""))


    @patch('api.app.fetch_news_from_feeds')
    @patch('api.app.process_articles')
    @patch('api.app.generate_mcqs_from_articles')
    def test_get_latest_mcqs_no_mcqs_generated(self, mock_generate_mcqs, mock_process_articles, mock_fetch_news):
        mock_fetch_news.return_value = MOCK_RAW_ARTICLES
        mock_process_articles.return_value = MOCK_PROCESSED_ARTICLES
        mock_generate_mcqs.return_value = [] # Simulate no MCQs generated

        response = self.client.get('/api/mcqs/latest')

        self.assertEqual(response.status_code, 200) # Success, but no content
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data['message'], "Articles fetched and processed, but no MCQs could be generated from the content.")
        self.assertEqual(data['data'], [])

    @patch('api.app.spacy_nlp', None) # Mock spacy_nlp as None to simulate model not loaded
    @patch('api.app.fetch_news_from_feeds')
    def test_get_latest_mcqs_spacy_model_not_loaded(self, mock_fetch_news):
        # This test specifically mocks the spacy_nlp object *within the api.app module*
        # to simulate the condition where the spaCy model isn't available at API runtime.
        
        mock_fetch_news.return_value = MOCK_RAW_ARTICLES # Fetching itself is fine

        response = self.client.get('/api/mcqs/latest')

        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn("Content processing module not initialized correctly (spaCy model missing)", data.get("error", ""))
        
    # Example of testing a general exception
    @patch('api.app.fetch_news_from_feeds', side_effect=Exception("Unexpected general error"))
    def test_get_latest_mcqs_unexpected_error(self, mock_fetch_news):
        response = self.client.get('/api/mcqs/latest')
        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn("An unexpected server error occurred: Unexpected general error", data.get("error", ""))


if __name__ == '__main__':
    # This allows running this test file directly,
    # but `python -m unittest discover tests` is preferred from project root.
    unittest.main()
