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
            
            // --- IMPROVED ERROR HANDLING ---
            // FastAPI validation errors are in `errorData.detail`.
            // It's usually an array of error objects.
            if (errorData.detail && Array.isArray(errorData.detail)) {
                // Format the error messages into a readable string.
                const messages = errorData.detail.map(err => {
                    // err.loc is an array like ["body", "fields", 0, "type"]
                    const field = err.loc.join(' -> '); 
                    return `${field}: ${err.msg}`; // e.g., "body -> fields -> 0 -> type: Input should be 'signature'..."
                });
                throw new Error(messages.join('\n'));
            }
            // Fallback for other types of errors
            throw new Error(errorData.detail || 'Failed to save template.');
            // --- END OF IMPROVEMENT ---
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

/**
 * Fetches the required data for a signer using their unique token.
 * @param {string} token The signing token from the URL.
 * @returns {Promise<Object>} The data needed for signing (envelopeId, fields).
 */
async function getSigningData(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/sign/${token}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to load signing data.');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching signing data:', error);
        throw error;
    }
}

/**
 * Submits the filled-out field data (signatures, text) to the backend.
 * @param {string} token The signing token.
 * @param {Object} submissionData The payload containing the field values.
 * @returns {Promise<Object>} The success message from the server.
 */
async function submitSignature(token, submissionData) {
    try {
        const response = await fetch(`${API_BASE_URL}/sign/${token}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(submissionData),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to submit signature.');
        }
        return await response.json();
    } catch (error) {
        console.error('Error submitting signature:', error);
        throw error;
    }
}

/**
 * Verifies a signed document by uploading it along with its envelope ID.
 * @param {string} envelopeId The ID of the envelope.
 * @param {File} file The signed PDF file to verify.
 * @returns {Promise<Object>} The verification result from the server.
 */
async function verifyDocument(envelopeId, file) {
    const formData = new FormData();
    formData.append('envelope_id', envelopeId);
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/verify/`, {
            method: 'POST',
            body: formData,
        });

        // For verification, we always want the JSON body, even on failure
        const resultData = await response.json();

        if (!response.ok) {
            throw new Error(resultData.detail || 'Verification request failed.');
        }

        return resultData;
    } catch (error) {
        console.error('Error verifying document:', error);
        throw error;
    }
}