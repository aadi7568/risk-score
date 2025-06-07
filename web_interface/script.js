async function generateScore() {
    const fileInput = document.getElementById('file-upload');
    const fileIdInput = document.getElementById('file-id');
    const scoreValue = document.getElementById('score-value');
    const riskIndicator = document.getElementById('risk-indicator');
    const riskyClauses = document.getElementById('risky-clauses');
    const clausesList = document.getElementById('clauses-list');
    const errorMessageArea = document.getElementById('error-message-area'); // Get the error message area
    const analyzedFilenameArea = document.getElementById('analyzed-filename-area'); // Get the filename area
    const analyzedFilenameDisplay = document.getElementById('analyzed-filename'); // Get the filename display paragraph

    // Clear previous results and errors
    scoreValue.textContent = 'Analyzing...';
    riskIndicator.style.left = '50%';
    riskyClauses.classList.add('hidden');
    clausesList.innerHTML = '';
    errorMessageArea.classList.add('hidden'); // Hide any previous error message
    errorMessageArea.innerHTML = ''; // Clear previous error message content


    try {
        if (!fileInput.files.length) {
            throw new Error('Please select a file to analyze');
        }

        const fileToUpload = fileInput.files[0];
        const selectedFileName = fileToUpload.name; // Store the selected filename

        const formData = new FormData();
        formData.append('file', fileToUpload, fileToUpload.name);

        console.log('Sending request to API...');
        const response = await fetch('http://localhost:8000/analyze', {
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            },
            mode: 'cors',
            credentials: 'omit',
            body: formData
        }).catch(error => {
            console.error('Network error:', error);
            // More general network/server error handling
            let userMessage = 'A network error occurred. Please ensure the API server is running.';
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                // This specific TypeError often indicates network connection issues or CORS problems
                userMessage = 'Could not connect to the API. Ensure the server is running and accessible at http://localhost:8000. If running locally, also check browser console for CORS issues.';
            } else {
                userMessage = `Network error: ${error.message}`;
            }
            // Rethrow the error with a more user-friendly message
            throw new Error(userMessage);
        });

        console.log('Response status:', response.status);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', errorText);
            // Handle API errors (e.g., 400, 500 status codes)
            let errorMessage = `API request failed with status ${response.status}.`;
            try {
                // Attempt to parse error details if the response is JSON
                const errorJson = JSON.parse(errorText);
                if (errorJson.detail) {
                    errorMessage += ` Details: ${errorJson.detail}`;
                } else {
                    errorMessage += ` Response: ${errorText}`;
                }
            } catch (e) {
                // If response is not JSON, just show the text
                errorMessage += ` Response: ${errorText}`;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('Received data:', data);

        // Update score display
        scoreValue.textContent = `${data.risk_score}%`;

        // Update risk indicator position (0-100 to percentage)
        riskIndicator.style.left = `${data.risk_score}%`;

        // Display risky clauses if any
        if (data.risky_clauses && data.risky_clauses.length > 0) {
            riskyClauses.classList.remove('hidden');

            clausesList.innerHTML = data.risky_clauses.map((clauseString, index) => {
                const parts = clauseString.split(' - ', 2);
                const clauseText = parts[0].trim();
                const explanation = parts.length > 1 && parts[1].trim() !== '' ? parts[1].trim() : 'Explanation not provided.';

                const sequentialNumber = index + 1;
                const category = data.risk_categories[index] || '-';
                const severity = data.clause_severity[index] || '-';

                let severityClass = '';
                switch (severity.toLowerCase()) {
                    case 'high risk':
                        severityClass = 'severity-high';
                        break;
                    case 'medium risk':
                        severityClass = 'severity-medium';
                        break;
                    case 'low risk':
                        severityClass = 'severity-low';
                        break;
                    default:
                        severityClass = 'severity-unknown';
                }

                return `
                <div class="p-4 bg-red-50 rounded-lg border border-red-200">
                    <div class="flex items-start">
                        <span class="flex-shrink-0 w-6 h-6 bg-red-100 text-red-800 rounded-full flex items-center justify-center font-medium mr-3">${sequentialNumber}</span>
                        <div class="flex-grow">
                            <p class="text-red-800 font-medium mb-1">${clauseText}</p>
                            <div class="flex items-center space-x-2 mb-2">
                                <span class="text-xs font-semibold px-2.5 py-0.5 rounded ${severityClass}">${severity}</span>
                                <span class="text-xs font-semibold px-2.5 py-0.5 rounded bg-gray-200 text-gray-800 category-tag">${category}</span>
                            </div>
                            <p class="text-red-600 text-sm">${explanation}</p>
                        </div>
                    </div>
                </div>
            `;
            }).join('');
        } else {
            riskyClauses.classList.add('hidden');
        }
        fileInput.value = ''; // Clear the file input

        // Display the filename of the successfully analyzed file
        analyzedFilenameDisplay.textContent = selectedFileName;
        analyzedFilenameArea.classList.remove('hidden');
    } catch (error) {
        console.error('Error details:', error);
        scoreValue.textContent = 'Error'; // Display a generic "Error" on the score
        riskIndicator.style.left = '50%'; // Reset indicator

        // Display error message in the dedicated area
        errorMessageArea.classList.remove('hidden');
        errorMessageArea.innerHTML = `
            <p class="font-medium">Analysis Failed:</p>
            <p class="mt-1 text-sm">${error.message}</p>
            ${error.message.includes('Could not connect to the API') ? `
            <p class="mt-2 text-sm font-semibold">Troubleshooting steps:</p>
            <ul class="mt-1 text-sm list-disc list-inside">
                <li>Ensure the API server is running at http://localhost:8000</li>
                <li>Check your browser's developer console (F12) for detailed network or CORS errors</li>
            </ul>
            ` : ''}
        `;

        riskyClauses.classList.add('hidden'); // Ensure risky clauses are hidden on error
        analyzedFilenameArea.classList.add('hidden'); // Hide filename area on error
    }
}