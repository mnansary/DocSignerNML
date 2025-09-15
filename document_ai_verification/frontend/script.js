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
                        // --- FIX: Move the try/catch to be more specific ---
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

        let stageContainer = document.getElementById(containerId);
        if (!stageContainer) {
            stageContainer = document.createElement('div');
            stageContainer.id = containerId;
            stageContainer.className = 'stage-container';
            stageContainer.innerHTML = `<h2>${stage_title}</h2>`;
            reportsContainer.appendChild(stageContainer);
        }

        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        
        // --- FIX: Render the correct data structure from PageHolisticAnalysis ---
        const requiredInputsHtml = result.required_inputs.length > 0
            ? result.required_inputs.map(item => `<li><strong>${item.input_type}:</strong> ${item.description}</li>`).join('')
            : '<li>None</li>';

        const prefilledInputsHtml = result.prefilled_inputs.length > 0
            ? result.prefilled_inputs.map(item => `<li><strong>${item.input_type} (${item.marker_text}):</strong> ${item.value}</li>`).join('')
            : '<li>None</li>';

        resultCard.innerHTML = `
            <div class="card-header">
                <h4>Page ${result.page_number}</h4>
            </div>
            <div class="card-content">
                <p><strong>Summary:</strong> ${result.summary || 'Not available.'}</p>
                <h5>Required Inputs</h5>
                <ul>${requiredInputsHtml}</ul>
                <h5>Prefilled Inputs</h5>
                <ul>${prefilledInputsHtml}</ul>
            </div>
        `;
        stageContainer.appendChild(resultCard);
    }
    
    function renderWorkflowComplete(data) {
        summarySection.classList.remove('hidden');
        finalStatusMessage.textContent = `${data.final_status}: ${data.message}`;
        finalStatusMessage.className = data.final_status.toLowerCase(); // 'success' or 'failure'
    }
});