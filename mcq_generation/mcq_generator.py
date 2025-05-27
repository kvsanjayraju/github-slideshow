import random

# --- Mock data for testing if content_processor.py is unavailable ---
# This data simulates the output of content_processor.process_articles
MOCK_PROCESSED_ARTICLES = [
    {
        "title": "PM Inaugurates New Highway",
        "link": "http://example.com/pm-highway-inauguration",
        "cleaned_text": "Prime Minister Narendra Modi inaugurated the new Delhi-Mumbai Expressway today. The project aims to reduce travel time. Union Minister Nitin Gadkari was also present. The expressway is a significant infrastructure development.",
        "sentences": [
            "Prime Minister Narendra Modi inaugurated the new Delhi-Mumbai Expressway today.",
            "The project aims to reduce travel time.",
            "Union Minister Nitin Gadkari was also present.",
            "The expressway is a significant infrastructure development."
        ],
        "named_entities": [
            ("Narendra Modi", "PERSON"),
            ("Delhi-Mumbai Expressway", "FAC"), # FAC for Facility, could be ORG or LOC depending on spaCy model
            ("today", "DATE"),
            ("Nitin Gadkari", "PERSON"),
        ],
        "keywords": ["Prime Minister Narendra Modi", "new Delhi-Mumbai Expressway", "Union Minister Nitin Gadkari", "travel time", "project", "significant infrastructure development"],
        "processing_status": "Successfully processed"
    },
    {
        "title": "RBI Announces New Monetary Policy",
        "link": "http://example.com/rbi-policy",
        "cleaned_text": "The Reserve Bank of India (RBI) announced its new monetary policy. Governor Shaktikanta Das stated that the repo rate remains unchanged. The focus is on controlling inflation. This decision was made by the Monetary Policy Committee.",
        "sentences": [
            "The Reserve Bank of India (RBI) announced its new monetary policy.",
            "Governor Shaktikanta Das stated that the repo rate remains unchanged.",
            "The focus is on controlling inflation.",
            "This decision was made by the Monetary Policy Committee."
        ],
        "named_entities": [
            ("The Reserve Bank of India", "ORG"),
            ("RBI", "ORG"),
            ("Shaktikanta Das", "PERSON"),
            ("Monetary Policy Committee", "ORG")
        ],
        "keywords": ["The Reserve Bank of India", "new monetary policy", "Governor Shaktikanta Das", "repo rate", "Monetary Policy Committee", "inflation"],
        "processing_status": "Successfully processed"
    }
]

# Define entity types that are good candidates for MCQ subjects
RELEVANT_ENTITY_TYPES = ["PERSON", "ORG", "GPE", "LOC", "FAC", "EVENT", "PRODUCT"]

def find_sentence_for_subject(subject: str, sentences: list) -> str | None:
    """
    Finds the first sentence containing the given subject.
    """
    for sentence in sentences:
        if subject in sentence:
            return sentence
    return None

def generate_distractors(subject: str, correct_sentence_part: str, article: dict, num_distractors: int = 3) -> list:
    """
    Generates distractors for an MCQ.
    This is a basic implementation and can be significantly improved.
    """
    distractors = set() # Use a set to avoid duplicate distractors initially

    # Strategy 1: Other named entities of similar type (if possible) or any type
    # For simplicity, we'll pick any other named entity first.
    for ent_text, ent_type in article.get("named_entities", []):
        if ent_text != subject and ent_text not in correct_sentence_part:
            distractors.add(ent_text)
            if len(distractors) >= num_distractors * 2: # Get more candidates initially
                break
    
    # Strategy 2: Other keywords
    for keyword in article.get("keywords", []):
        if keyword != subject and keyword not in correct_sentence_part:
            # Simple check to avoid adding parts of the correct answer as distractors
            if not any(kw_part in correct_sentence_part for kw_part in keyword.split()):
                 distractors.add(keyword)
        if len(distractors) >= num_distractors * 3: # Get more candidates
            break

    # Fallback: if not enough distractors, use parts of other sentences (very naive)
    if len(distractors) < num_distractors:
        for sent in article.get("sentences", []):
            if correct_sentence_part not in sent: # Avoid the sentence with the correct answer
                words = sent.split()
                if len(words) > 2: # Pick a short phrase
                    distractors.add(" ".join(words[:3]))
            if len(distractors) >= num_distractors:
                break
    
    # Ensure distractors are not too similar to the correct answer or the subject
    final_distractors = [d for d in list(distractors) if d.lower() != correct_sentence_part.lower() and d.lower() != subject.lower()]

    # If still not enough, add some generic placeholders (should be improved)
    generic_placeholders = ["Information not available in this article.", "Another related concept.", "A different policy aspect."]
    i = 0
    while len(final_distractors) < num_distractors and i < len(generic_placeholders):
        if generic_placeholders[i] not in final_distractors and generic_placeholders[i] != correct_sentence_part:
            final_distractors.append(generic_placeholders[i])
        i += 1
        
    return random.sample(final_distractors, min(len(final_distractors), num_distractors))


def generate_mcqs_from_articles(processed_articles: list) -> list:
    """
    Generates Multiple Choice Questions (MCQs) from a list of processed news articles.

    Args:
        processed_articles (list): A list of dictionaries, where each dictionary
                                   is a processed news item.

    Returns:
        list: A list of MCQ dictionaries.
    """
    all_mcqs = []
    mcqs_per_article_target = 2 

    for article in processed_articles:
        if article.get("processing_status") != "Successfully processed":
            print(f"Skipping article due to processing status: {article.get('title', 'N/A')}")
            continue

        mcqs_generated_for_this_article = 0
        potential_subjects = []

        # Gather potential subjects from named entities
        for entity_text, entity_type in article.get("named_entities", []):
            if entity_type in RELEVANT_ENTITY_TYPES:
                potential_subjects.append({"text": entity_text, "type": entity_type, "is_entity": True})
        
        # Gather potential subjects from keywords (if not already an entity)
        entity_texts = {s["text"] for s in potential_subjects}
        for keyword in article.get("keywords", []):
            if keyword not in entity_texts:
                potential_subjects.append({"text": keyword, "type": "KEYWORD", "is_entity": False})
        
        random.shuffle(potential_subjects) # Shuffle to get variety if we cap MCQs per article

        for subject_info in potential_subjects:
            if mcqs_generated_for_this_article >= mcqs_per_article_target:
                break

            subject = subject_info["text"]
            subject_type = subject_info["type"]

            key_sentence = find_sentence_for_subject(subject, article.get("sentences", []))

            if key_sentence:
                # Formulate question stem
                if subject_type == "PERSON":
                    question_stem = f"Who is {subject}?"
                elif subject_type in ["ORG", "GPE", "FAC"]:
                    question_stem = f"What is {subject}?"
                else: # Default for other entities or keywords
                    question_stem = f"What is related to {subject}?"
                
                # For this basic version, the key_sentence itself (or a part of it) will be the correct answer.
                # More advanced: extract the specific information about the subject from the sentence.
                correct_answer_text = key_sentence 
                
                # Attempt to make the correct answer more concise if it's the full sentence
                # This is still very basic.
                if len(correct_answer_text.split()) > 15: # If sentence is long
                    # Try to find a clause or part containing the subject
                    parts = correct_answer_text.split(subject)
                    if len(parts) > 1:
                        # Combine subject with the part after it, up to a certain length
                        correct_answer_text = subject + parts[1].split('.')[0] # take up to first period if exists
                        if len(correct_answer_text.split()) > 15 : # if still too long, just use subject
                             correct_answer_text = subject + " (further details in article)"


                distractors = generate_distractors(subject, correct_answer_text, article)

                if len(distractors) < 3:
                    # print(f"Could not generate enough distractors for '{subject}' in article '{article['title']}'. Skipping MCQ.")
                    continue

                options = [correct_answer_text] + distractors
                random.shuffle(options)

                mcq = {
                    "question": question_stem,
                    "options": options,
                    "correct_answer_text": correct_answer_text, # Store the original correct statement
                    "source_article_title": article.get("title", "N/A"),
                    "source_article_link": article.get("link", "N/A")
                }
                all_mcqs.append(mcq)
                mcqs_generated_for_this_article += 1
        
    print(f"\nGenerated a total of {len(all_mcqs)} MCQs.")
    return all_mcqs


if __name__ == "__main__":
    print("--- Starting MCQ Generation Demo ---")

    articles_for_mcq = []
    try:
        # Try to use the actual data processing pipeline
        from data_processing.news_fetcher import fetch_news_from_feeds
        from data_processing.content_processor import process_articles
        
        print("\nStep 1: Fetching live news items...")
        raw_articles = fetch_news_from_feeds()
        
        if raw_articles:
            print(f"Fetched {len(raw_articles)} raw articles.")
            print("\nStep 2: Processing articles...")
            articles_for_mcq = process_articles(raw_articles)
            if not articles_for_mcq or articles_for_mcq[0].get("processing_status") != "Successfully processed":
                print("Processing failed or no articles processed successfully by content_processor. Using mock data.")
                articles_for_mcq = MOCK_PROCESSED_ARTICLES
        else:
            print("No raw articles fetched. Using mock processed data.")
            articles_for_mcq = MOCK_PROCESSED_ARTICLES

    except ImportError:
        print("Could not import from 'data_processing' module. Using mock processed data.")
        articles_for_mcq = MOCK_PROCESSED_ARTICLES
    except Exception as e:
        print(f"An error occurred during data fetching/processing: {e}. Using mock processed data.")
        articles_for_mcq = MOCK_PROCESSED_ARTICLES

    if not articles_for_mcq:
        print("\nNo data (live or mock) available to generate MCQs. Exiting demo.")
    else:
        print(f"\nStep 3: Generating MCQs from {len(articles_for_mcq)} processed articles...")
        generated_mcqs = generate_mcqs_from_articles(articles_for_mcq)

        if generated_mcqs:
            print(f"\n--- Sample Generated MCQs ({min(3, len(generated_mcqs))} of them) ---")
            for i, mcq in enumerate(generated_mcqs[:3]):
                print(f"\nMCQ {i+1}:")
                print(f"  Question: {mcq['question']}")
                print(f"  Options:")
                for opt_idx, option in enumerate(mcq['options']):
                    print(f"    {chr(97+opt_idx)}) {option}")
                print(f"  Correct Answer Statement: {mcq['correct_answer_text']}")
                print(f"  Source: {mcq['source_article_title']} ({mcq['source_article_link']})")
        else:
            print("\nNo MCQs were generated.")
            print("This could be due to:")
            print("  - No suitable subjects found in the articles.")
            print("  - Inability to generate enough distinct distractors.")
            print("  - Articles not being processed successfully (e.g., spaCy model missing).")

    print("\n--- MCQ Generation Demo Finished ---")
    print("Note: Distractor generation is basic. For better quality, more sophisticated NLP techniques are needed.")
