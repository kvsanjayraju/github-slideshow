document.addEventListener('DOMContentLoaded', () => {
    const loadMcqsBtn = document.getElementById('loadMcqsBtn');
    const mcqContainer = document.getElementById('mcq-container');
    const statusMessage = document.getElementById('status-message');

    const API_URL = 'http://localhost:5000/api/mcqs/latest';

    async function fetchAndDisplayMcqs() {
        // Clear previous MCQs and status messages
        mcqContainer.innerHTML = '';
        statusMessage.textContent = 'Loading MCQs...';
        loadMcqsBtn.disabled = true;

        try {
            const response = await fetch(API_URL);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: "Unknown API error" }));
                throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorData.error || errorData.message}`);
            }

            const data = await response.json();

            if (data.error) { // Handle cases where API returns a 2xx but with an error message in JSON
                statusMessage.textContent = `Error: ${data.error}`;
                console.error('Error from API:', data.error);
                return;
            }
            
            if (data.mcqs && data.mcqs.length > 0) {
                statusMessage.textContent = `Successfully loaded ${data.mcqs.length} MCQs.`;
                displayMcqs(data.mcqs);
            } else {
                statusMessage.textContent = 'No MCQs available at the moment. Try again later.';
            }

        } catch (error) {
            console.error('Failed to fetch MCQs:', error);
            statusMessage.textContent = `Failed to load MCQs. ${error.message}. Please ensure the backend API is running.`;
        } finally {
            loadMcqsBtn.disabled = false;
        }
    }

    function displayMcqs(mcqs) {
        mcqs.forEach((mcq, index) => {
            const mcqItem = document.createElement('div');
            mcqItem.classList.add('mcq-item');

            const questionElement = document.createElement('h3');
            questionElement.textContent = `Q${index + 1}: ${mcq.question}`;
            mcqItem.appendChild(questionElement);

            const optionsList = document.createElement('ul');
            mcq.options.forEach((option, optionIndex) => {
                const optionItem = document.createElement('li');
                
                // Using radio buttons for options
                const radioInput = document.createElement('input');
                radioInput.type = 'radio';
                radioInput.name = `mcq-${index}`; // Unique name for each question's radio group
                radioInput.id = `mcq-${index}-opt-${optionIndex}`;
                radioInput.value = option;

                const label = document.createElement('label');
                label.htmlFor = `mcq-${index}-opt-${optionIndex}`;
                label.textContent = option;
                
                optionItem.appendChild(radioInput);
                optionItem.appendChild(label);
                optionsList.appendChild(optionItem);
            });
            mcqItem.appendChild(optionsList);

            // Optionally, display the correct answer (for learning purposes, can be hidden)
            // const correctAnswerElement = document.createElement('p');
            // correctAnswerElement.innerHTML = `<strong>Correct Answer (Hint):</strong> ${mcq.correct_answer_text}`;
            // mcqItem.appendChild(correctAnswerElement);

            const sourceElement = document.createElement('p');
            sourceElement.style.fontSize = '0.9em';
            sourceElement.style.color = '#555';
            sourceElement.innerHTML = `<em>Source: <a href="${mcq.source_article_link}" target="_blank">${mcq.source_article_title}</a></em>`;
            mcqItem.appendChild(sourceElement);
            
            mcqContainer.appendChild(mcqItem);
        });
    }

    if (loadMcqsBtn) {
        loadMcqsBtn.addEventListener('click', fetchAndDisplayMcqs);
    }

    // Instructions on how to run the application:
    // 1. Ensure the backend API is running:
    //    - Navigate to the 'api' directory in your terminal.
    //    - Run the Flask app using a command like `python app.py` or `flask run`.
    //    - The API should then be available at http://localhost:5000.
    // 2. Open the `frontend/index.html` file in your web browser.
    // 3. Click the "Load Latest MCQs" button to fetch and display the MCQs from the API.
    // Note: If you encounter CORS issues when running index.html directly from the filesystem,
    // you might need to serve the frontend files using a simple HTTP server,
    // or configure CORS on the Flask backend if deploying to different domains.
    // For local development, opening `index.html` directly often works if the API is on localhost.
});
