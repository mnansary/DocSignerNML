// A simple API client to communicate with the backend.

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'; // Your FastAPI server URL

/**
 * Uploads a PDF file to create a new envelope.
 * @param {File} file The PDF file to upload.
 * @returns {Promise<Object>} The JSON response from the server (e.g., { id: "envelope_uuid" }).
 */
async function createEnvelope(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/envelopes/`, {
            method: 'POST',
            body: formData,
            // Note: 'Content-Type' is not set here, the browser will automatically
            // set it to 'multipart/form-data' along with the boundary.
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to upload file.');
        }

        return await response.json();
    } catch (error) {
        console.error('Error creating envelope:', error);
        throw error;
    }
}

// We will add more functions here later for setup, signing, and verification.
// Add these functions to your existing apiClient.js file

/**
 * Gets a PNG preview of a specific document page.
 * @param {string} envelopeId The ID of the envelope.
 * @param {number} pageNum The page number to retrieve.
 * @returns {Promise<Blob>} A blob representing the PNG image.
 */
async function getPagePreview(envelopeId, pageNum) {
    try {
        const response = await fetch(`${API_BASE_URL}/envelopes/${envelopeId}/preview/${pageNum}`);
        if (!response.ok) {
            throw new Error('Failed to load page preview.');
        }
        return await response.blob();
    } catch (error) {
        console.error('Error fetching page preview:', error);
        throw error;
    }
}

/**
 * Sends the template configuration (recipients and fields) to the backend.
 * @param {string} envelopeId The ID of the envelope.
 * @param {Object} setupData The setup data, including recipients and fields.
 * @returns {Promise<Object>} The JSON response from the server.
 */
async function setupEnvelope(envelopeId, setupData) {
    try {
        const response = await fetch(`${API_BASE_URL}/envelopes/${envelopeId}/setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(setupData),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to save template.');
        }
        return await response.json();
    } catch (error) {
        console.error('Error setting up envelope:', error);
        throw error;
    }
}

/**
 * Triggers the backend to send the envelope for signing.
 * @param {string} envelopeId The ID of the envelope to send.
 * @returns {Promise<Object>} The JSON response from the server.
 */
async function sendEnvelope(envelopeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/envelopes/${envelopeId}/send`, {
            method: 'POST',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to send envelope.');
        }
        return await response.json();
    } catch (error) {
        console.error('Error sending envelope:', error);
        throw error;
    }
}

/**
 * Fetches the original PDF document file itself.
 * @param {string} envelopeId The ID of the envelope.
 * @returns {Promise<ArrayBuffer>} The raw PDF file data.
 */
async function getOriginalPdf(envelopeId) {
    try {
        // This is a new backend endpoint we will create
        const response = await fetch(`${API_BASE_URL}/envelopes/${envelopeId}/download`);
        if (!response.ok) {
            throw new Error('Failed to download original PDF.');
        }
        return await response.arrayBuffer();
    } catch (error) {
        console.error('Error fetching original PDF:', error);
        throw error;
    }
}