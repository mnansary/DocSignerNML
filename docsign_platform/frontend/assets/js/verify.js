document.addEventListener('DOMContentLoaded', () => {
    const verifyForm = document.getElementById('verify-form');
    const envelopeIdInput = document.getElementById('envelope-id');
    const pdfFileInput = document.getElementById('pdf-file');
    const verifyButton = document.getElementById('verify-button');
    const fileNameDisplay = document.getElementById('file-name-display');
    const resultContainer = document.getElementById('result-container');
    const resultMessage = document.getElementById('result-message');

    pdfFileInput.addEventListener('change', () => {
        if (pdfFileInput.files.length > 0) {
            fileNameDisplay.textContent = pdfFileInput.files[0].name;
        } else {
            fileNameDisplay.textContent = 'Choose the signed PDF file...';
        }
    });

    verifyForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const envelopeId = envelopeIdInput.value;
        const file = pdfFileInput.files[0];

        if (!envelopeId || !file) {
            displayResult('Please provide both an Envelope ID and a file.', 'error');
            return;
        }

        verifyButton.disabled = true;
        verifyButton.textContent = 'Verifying...';
        resultContainer.style.display = 'none';

        try {
            const result = await verifyDocument(envelopeId, file);
            
            if (result.is_authentic) {
                displayResult(result.message, 'success');
            } else {
                displayResult(result.message, 'error');
            }
        } catch (error) {
            displayResult(error.message, 'error');
        } finally {
            verifyButton.disabled = false;
            verifyButton.textContent = 'Verify Document';
        }
    });

    function displayResult(message, type) {
        resultContainer.style.display = 'block';
        resultMessage.textContent = message;
        resultMessage.className = `status ${type}`;
    }
});