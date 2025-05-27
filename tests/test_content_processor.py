import unittest
import spacy
from data_processing.content_processor import process_articles

# --- Global variable to store the loaded spaCy model ---
NLP_MODEL = None

def setUpModule():
    """
    Load the spaCy model once before any tests in this module run.
    This is more efficient than loading it for each test case or class.
    """
    global NLP_MODEL
    try:
        NLP_MODEL = spacy.load("en_core_web_sm")
        print("spaCy model 'en_core_web_sm' loaded successfully for testing.")
    except OSError:
        print("Failed to load spaCy model 'en_core_web_sm'. Some tests will be skipped.")
        print("Please run: python -m spacy download en_core_web_sm")
        NLP_MODEL = None # Ensure it's None if loading fails

@unittest.skipIf(NLP_MODEL is None, "spaCy model 'en_core_web_sm' not available. Skipping ContentProcessor tests.")
class TestContentProcessor(unittest.TestCase):

    def setUp(self):
        """
        Pass the globally loaded model to the content_processor module.
        This assumes content_processor.py uses a global 'nlp' variable,
        or is refactored to accept an nlp object.
        For this example, we'll assume data_processing.content_processor.nlp can be set.
        """
        # The content_processor.py script already tries to load the model itself.
        # If it's loaded here, we are ensuring the test environment uses the same model.
        # If content_processor.nlp is already loaded by its own import, this might be redundant
        # but helps ensure test isolation if that module's loading failed for some reason.
        import data_processing.content_processor
        data_processing.content_processor.nlp = NLP_MODEL


    def test_html_cleaning(self):
        article = {
            "summary": "<p>This is a <b>bold</b> statement.</p> &nbsp; With extra spaces. \nNewlines too."
        }
        processed = process_articles([article])
        self.assertEqual(processed[0]["cleaned_text"], "This is a bold statement. With extra spaces. Newlines too.")

    def test_sentence_segmentation(self):
        article = {
            "summary": "First sentence. Second sentence! Is this the third? Yes, it is."
        }
        processed = process_articles([article])
        self.assertEqual(len(processed[0]["sentences"]), 4)
        self.assertEqual(processed[0]["sentences"][0], "First sentence.")
        self.assertEqual(processed[0]["sentences"][1], "Second sentence!")
        self.assertEqual(processed[0]["sentences"][2], "Is this the third?")
        self.assertEqual(processed[0]["sentences"][3], "Yes, it is.")


    def test_ner_extraction(self):
        article = {
            "summary": "Elon Musk visited Mars with SpaceX on Tuesday in New York."
        }
        processed = process_articles([article])
        entities = processed[0]["named_entities"]
        
        # Note: Exact entity labels can vary slightly based on spaCy model version & context
        expected_entities_texts = {"Elon Musk", "Mars", "SpaceX", "Tuesday", "New York"}
        extracted_entities_texts = {ent[0] for ent in entities}
        
        self.assertTrue(expected_entities_texts.issubset(extracted_entities_texts),
                        f"Expected {expected_entities_texts}, got {extracted_entities_texts}")

        # Check for specific entities and their likely types
        self.assertTrue(any(ent[0] == "Elon Musk" and ent[1] == "PERSON" for ent in entities))
        self.assertTrue(any(ent[0] == "Mars" and ent[1] == "LOC" for ent in entities)) # Mars can be LOC or FAC
        self.assertTrue(any(ent[0] == "SpaceX" and ent[1] == "ORG" for ent in entities))
        self.assertTrue(any(ent[0] == "Tuesday" and ent[1] == "DATE" for ent in entities))
        self.assertTrue(any(ent[0] == "New York" and (ent[1] == "GPE" or ent[1] == "LOC") for ent in entities)) # New York can be GPE or LOC

    def test_keyword_extraction_noun_chunks(self):
        article = {
            "summary": "The new policy on renewable energy was announced by the Ministry of Power."
        }
        processed = process_articles([article])
        keywords = processed[0]["keywords"] # Based on noun chunks
        
        # Expected noun chunks can vary, but these are likely
        expected_keywords_subset = {"the new policy", "renewable energy", "the Ministry of Power"}
        # Convert list of keywords to a set for subset comparison
        self.assertTrue(expected_keywords_subset.issubset(set(keywords)),
                        f"Expected subset {expected_keywords_subset}, got {keywords}")

    def test_overall_processing_adds_keys(self):
        article = {
            "title": "Test Article",
            "link": "http://example.com/test",
            "published": "2024-01-01",
            "summary": "This is a simple summary for testing. Dr. Smith from Google is here."
        }
        processed = process_articles([article])
        self.assertEqual(len(processed), 1)
        processed_article = processed[0]

        self.assertIn("cleaned_text", processed_article)
        self.assertIn("sentences", processed_article)
        self.assertIn("named_entities", processed_article)
        self.assertIn("keywords", processed_article)
        self.assertIn("processing_status", processed_article)
        self.assertEqual(processed_article["processing_status"], "Successfully processed")
        
        self.assertEqual(processed_article["cleaned_text"], "This is a simple summary for testing. Dr. Smith from Google is here.")
        self.assertTrue(len(processed_article["sentences"]) >= 2)
        self.assertTrue(any(ent[0] == "Smith" for ent in processed_article["named_entities"])) # Check if "Smith" is an entity
        self.assertTrue(any(ent[0] == "Google" and ent[1] == "ORG" for ent in processed_article["named_entities"]))


    def test_processing_with_empty_summary(self):
        article = {
            "title": "Empty Summary Test",
            "summary": ""
        }
        processed = process_articles([article])
        self.assertEqual(processed[0]["cleaned_text"], "")
        self.assertEqual(len(processed[0]["sentences"]), 0)
        self.assertEqual(len(processed[0]["named_entities"]), 0)
        self.assertEqual(len(processed[0]["keywords"]), 0)
        self.assertEqual(processed[0]["processing_status"], "Skipped: No summary")

    def test_processing_with_missing_summary_key(self):
        article = {
            "title": "Missing Summary Test"
            # no "summary" key
        }
        processed = process_articles([article])
        self.assertEqual(processed[0]["cleaned_text"], "") # Default empty string
        self.assertEqual(processed[0]["sentences"], [])
        self.assertEqual(processed[0]["named_entities"], [])
        self.assertEqual(processed[0]["keywords"], [])
        self.assertEqual(processed[0]["processing_status"], "Skipped: No summary")

if __name__ == '__main__':
    unittest.main()
