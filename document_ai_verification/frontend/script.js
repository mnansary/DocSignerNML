// --- Global function to open the image difference viewer ---
// This is placed outside the main event listener to be accessible from inline 'onclick' attributes.
function showDifferenceViewer(originalUrl, signedUrl) {
    const newWindow = window.open('', '_blank');
    if (newWindow) {
        newWindow.document.write(`
            <html>
                <head>
                    <title>Document Difference Viewer</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 0; background-color: #343a40; color: #f8f9fa; }
                        h1 { text-align: center; padding: 15px; background-color: #212529; margin: 0;}
                        .viewer-container { display: flex; justify-content: space-around; padding: 20px; gap: 20px; align-items: flex-start; }
                        .image-wrapper { flex: 1; border: 1px solid #6c757d; box-shadow: 0 4px 12px rgba(0,0,0,0.2); background-color: #495057; }
                        .image-wrapper h2 { text-align: center; background-color: #212529; margin: 0; padding: 12px; border-bottom: 1px solid #6c757d; font-size: 1.2rem; }
                        .image-wrapper img { width: 100%; display: block; }
                        .original h2 { color: #28a745; } /* Green */
                        .signed h2 { color: #dc3545; } /* Red */
                    </style>
                </head>
                <body>
                    <h1>Visual Comparison</h1>
                    <div class="viewer-container">
                        <div class="image-wrapper original">
                            <h2>Original (Changes in Green)</h2>
                            <img src="${originalUrl}" alt="Original document page with differences highlighted in green">
                        </div>
                        <div class="image-wrapper signed">
                            <h2>Signed (Changes in Red)</h2>
                            <img src="${signedUrl}" alt="Signed document page with differences highlighted in red">
                        </div>
                    </div>
                </body>
            </html>
        `);
        newWindow.document.close();
    } else {
        alert("Please allow popups for this site to view the difference images.");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const nsvFileInput = document.getElementById('nsv-file');
    const svFileInput = document.getElementById('sv-file');
    const nsvFileName = document.getElementById('nsv-file-name');
    const svFileName = document.getElementById('sv-file-name');
    const verifyButton = document.getElementById('verify-button');

    // --- Output Area References ---
    const outputContainer = document.getElementById('output-container');
    const logSection = document.getElementById('log-section');
    const logStream = document.getElementById('log-stream');
    const reportsContainer = document.getElementById('reports-container');
    const summarySection = document.getElementById('summary-section');
    const finalStatusMessage = document.getElementById('final-status-message');

    // --- File Input Handling ---
    function checkFilesAndEnableButton() {
        const nsvReady = nsvFileInput.files.length > 0;
        const svReady = svFileInput.files.length > 0;
        verifyButton.disabled = !(nsvReady && svReady);
    }

    nsvFileInput.addEventListener('change', () => {
        if (nsvFileInput.files.length > 0) {
            nsvFileName.textContent = nsvFileInput.files[0].name;
            nsvFileName.classList.add('selected');
        } else {
            nsvFileName.textContent = 'Click or drop file here';
            nsvFileName.classList.remove('selected');
        }
        checkFilesAndEnableButton();
    });

    svFileInput.addEventListener('change', () => {
        if (svFileInput.files.length > 0) {
            svFileName.textContent = svFileInput.files[0].name;
            svFileName.classList.add('selected');
        } else {
            svFileName.textContent = 'Click or drop file here';
            svFileName.classList.remove('selected');
        }
        checkFilesAndEnableButton();
    });

    // --- Main Verification Logic ---
    verifyButton.addEventListener('click', async () => {
        resetUI();

        const formData = new FormData();
        formData.append('nsv_file', nsvFileInput.files[0]);
        formData.append('sv_file', svFileInput.files[0]);

        try {
            const response = await fetch('/verify/', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server Error: ${response.status}`);
            }
            
            await processStream(response);

        } catch (error) {
            handleEvent({ type: 'error', message: `Client-side error: ${error.message}` });
        }
    });

    // --- UI Management Functions ---
    function resetUI() {
        verifyButton.disabled = true;
        verifyButton.textContent = 'Processing...';
        
        outputContainer.classList.remove('hidden');
        logStream.textContent = '';
        reportsContainer.innerHTML = '';
        summarySection.classList.add('hidden');
        finalStatusMessage.textContent = '';
    }

    function addLogMessage(message, isError = false) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.textContent = `[${timestamp}] ${message}`;
        if (isError) {
            logEntry.classList.add('error');
        }
        logStream.appendChild(logEntry);
        logStream.scrollTop = logStream.scrollHeight; // Auto-scroll
    }

    // --- Stream Processing ---
    async function processStream(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                 addLogMessage("Stream finished.");
                 break;
            }

            buffer += decoder.decode(value, { stream: true });
            
            const parts = buffer.split('\n\n');
            buffer = parts.pop(); // Keep the last, possibly incomplete, part

            for (const part of parts) {
                if (part.startsWith('data:')) {
                    const jsonString = part.substring(5).trim();
                    if (!jsonString) continue;

                    try {
                        const event = JSON.parse(jsonString);
                        try {
                           handleEvent(event);
                        } catch (renderError) {
                            console.error("Error rendering event data:", renderError);
                            handleEvent({ type: 'error', message: `Failed to render UI for event: ${renderError.message}` });
                        }
                    } catch (parseError) {
                        console.error('Failed to parse JSON from stream:', jsonString);
                        handleEvent({ type: 'error', message: 'Received malformed data from server.' });
                    }
                }
            }
        }
    }

    // --- Event Handling ---
    function handleEvent(event) {
        switch (event.type) {
            case 'status_update':
                addLogMessage(event.message);
                break;
            case 'process_step_result':
                renderProcessStep(event.data);
                break;
            case 'workflow_complete':
                renderWorkflowComplete(event.data);
                verifyButton.disabled = false;
                verifyButton.textContent = 'Verify Again';
                break;
            // --- NEW CASE ADDED HERE ---
            case 'verification_failed':
                addLogMessage(`Workflow failed: ${event.data.message}`, true);
                renderWorkflowComplete(event.data); // Re-use the same UI logic for the final summary
                verifyButton.disabled = false;
                verifyButton.textContent = 'Verification Failed. Retry?';
                break;
            case 'error':
                addLogMessage(event.message, true);
                verifyButton.disabled = false;
                verifyButton.textContent = 'Verification Failed. Retry?';
                break;
            default:
                console.warn('Received unknown event type:', event.type);
        }
    }
    
    // --- Dynamic HTML Rendering ---
    function renderProcessStep(data) {
        const { stage_id, stage_title, result } = data;
        const containerId = `results-container-${stage_id}`;

        // 1. Find or create the container for this stage
        let stageContainer = document.getElementById(containerId);
        if (!stageContainer) {
            stageContainer = document.createElement('div');
            stageContainer.id = containerId;
            stageContainer.className = 'stage-container';
            stageContainer.innerHTML = `<h2>${stage_title}</h2>`;
            reportsContainer.appendChild(stageContainer);
        }

        // 2. Create the result card
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        let cardContentHtml = '';

        // 3. Use a switch to generate the correct HTML for each stage
        switch (stage_id) {
            case 'requirement_analysis':
                const requiredInputsHtml = result.required_inputs.length > 0
                    ? result.required_inputs.map(item => `<li><strong>${item.input_type}:</strong> ${item.description}</li>`).join('')
                    : '<li>None</li>';

                const prefilledInputsHtml = result.prefilled_inputs.length > 0
                    ? result.prefilled_inputs.map(item => `<li><strong>${item.input_type} (${item.marker_text}):</strong> ${item.value}</li>`).join('')
                    : '<li>None</li>';
                
                cardContentHtml = `
                    <div class="card-header"><h4>Page ${result.page_number}</h4></div>
                    <div class="card-content">
                        <p><strong>Summary:</strong> ${result.summary || 'Not available.'}</p>
                        <h5>Required Inputs</h5>
                        <ul>${requiredInputsHtml}</ul>
                        <h5>Prefilled Inputs</h5>
                        <ul>${prefilledInputsHtml}</ul>
                    </div>
                `;
                break;

            case 'content_verification':
                const status = result.verification_status; // "Verified", "Discrepancy-Found", "Needs-Review"
                const statusText = status.replace('-', ' '); // "Discrepancy Found"
                const statusClass = `status-${status.toLowerCase()}`; // "status-verified", "status-discrepancy-found", etc.
                let buttonHtml = '';

                if (status === 'Discrepancy-Found' && result.original_diff_url && result.signed_diff_url) {
                    const originalUrl = result.original_diff_url.replace(/"/g, '&quot;');
                    const signedUrl = result.signed_diff_url.replace(/"/g, '&quot;');
                    buttonHtml = `<button class="mismatch-button" onclick='showDifferenceViewer("${originalUrl}", "${signedUrl}")'>Show Discrepancy</button>`;
                }

                cardContentHtml = `
                    <div class="card-header">
                        <h4>Page ${result.page_number}</h4>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <div class="card-content">
                        <p><strong>Analysis:</strong> ${result.summary}</p>
                        ${buttonHtml}
                    </div>
                `;
                break;
            
            default:
                cardContentHtml = `<div class="card-content"><p>Unknown result type for stage: ${stage_id}</p></div>`;
        }

        resultCard.innerHTML = cardContentHtml;
        stageContainer.appendChild(resultCard);
    }
    
    function renderWorkflowComplete(data) {
        summarySection.classList.remove('hidden');
        finalStatusMessage.textContent = `${data.final_status}: ${data.message}`;
        finalStatusMessage.className = data.final_status.toLowerCase(); // 'success' or 'failure'
    }
});