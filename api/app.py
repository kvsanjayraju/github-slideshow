import sys
import os
from flask import Flask, jsonify

# --- System Path Modification ---
# Add the parent directory to the system path to allow imports from sibling directories
# (e.g., data_processing, mcq_generation)
# This is a common way to handle imports in a simple project structure.
# For more complex projects, packaging (e.g., using setup.py or pyproject.toml) is recommended.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- Module Imports ---
# Import necessary functions from the project's modules
try:
    from data_processing.news_fetcher import fetch_news_from_feeds
    from data_processing.content_processor import process_articles, nlp as spacy_nlp
    from mcq_generation.mcq_generator import generate_mcqs_from_articles
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure that all modules (news_fetcher, content_processor, mcq_generator) are in the correct directories (data_processing, mcq_generation) and that their dependencies are installed.")
    print("You might need to run: pip install -r requirements.txt")
    print("If using spaCy, ensure the model is downloaded: python -m spacy download en_core_web_sm")
    # Exit if essential modules cannot be imported, as the API cannot function.
    sys.exit(1)


# --- Flask Application Initialization ---
app = Flask(__name__)

# --- API Endpoint Definition ---
@app.route('/api/mcqs/latest', methods=['GET'])
def get_latest_mcqs():
    """
    API endpoint to fetch the latest news articles, process them,
    and generate MCQs.
    """
    try:
        # Step 1: Fetch news articles
        print("Fetching latest news articles...")
        raw_articles = fetch_news_from_feeds()
        if not raw_articles:
            print("No articles fetched.")
            return jsonify({"error": "Could not fetch any news articles. Please check RSS feed URLs or network connectivity."}), 500

        print(f"Fetched {len(raw_articles)} raw articles.")

        # Step 2: Process articles
        # Check if spaCy model loaded correctly in content_processor
        if spacy_nlp is None:
            print("spaCy model not loaded. Cannot process articles for MCQ generation.")
            return jsonify({"error": "Content processing module not initialized correctly (spaCy model missing). Cannot generate MCQs."}), 500
            
        print("Processing articles...")
        processed_articles = process_articles(raw_articles)
        if not processed_articles or any(article.get("processing_status") != "Successfully processed" for article in processed_articles if article.get("summary")): # Check if any valid article was processed
            # Filter out articles that were skipped due to no summary, then check processing status
            valid_articles_to_check = [art for art in processed_articles if art.get("summary")]
            if not valid_articles_to_check or all(art.get("processing_status") != "Successfully processed" for art in valid_articles_to_check):
                print("No articles were successfully processed.")
                return jsonify({"error": "Failed to process the fetched articles. Content processing might have failed."}), 500
        
        successfully_processed_articles = [p_art for p_art in processed_articles if p_art.get("processing_status") == "Successfully processed"]
        if not successfully_processed_articles:
            print("No articles were successfully processed after filtering.")
            return jsonify({"error": "No articles were successfully processed. Cannot generate MCQs."}), 500

        print(f"Successfully processed {len(successfully_processed_articles)} articles.")

        # Step 3: Generate MCQs
        print("Generating MCQs...")
        mcqs = generate_mcqs_from_articles(successfully_processed_articles)
        if not mcqs:
            print("No MCQs were generated.")
            return jsonify({"message": "Articles fetched and processed, but no MCQs could be generated from the content.", "data": []}), 200 # Success, but no content

        print(f"Generated {len(mcqs)} MCQs.")
        return jsonify({"message": "MCQs generated successfully", "mcqs": mcqs}), 200

    except Exception as e:
        # General error handler for unexpected issues during the process
        print(f"An unexpected error occurred in /api/mcqs/latest: {e}")
        # Log the full traceback for debugging if possible (e.g., using app.logger.exception(e))
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500

# --- Main Block to Run Flask Development Server ---
if __name__ == '__main__':
    # Note: It's crucial to ensure the spaCy model is downloaded before running.
    # The content_processor.py script has a check, but the API will fail if it's not available.
    if spacy_nlp is None:
        print("CRITICAL: spaCy model ('en_core_web_sm') is not loaded.")
        print("The API cannot function without it. Please download it by running:")
        print("python -m spacy download en_core_web_sm")
        print("Exiting.")
    else:
        print("Starting Flask development server...")
        # Host '0.0.0.0' makes the server accessible externally (e.g., within a Docker container or local network)
        # Debug=True is useful for development but should be turned off in production.
        app.run(host='0.0.0.0', port=5000, debug=True)
