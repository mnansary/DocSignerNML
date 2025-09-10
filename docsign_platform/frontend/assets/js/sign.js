document.addEventListener('DOMContentLoaded', () => {
    // --- STATE ---
    const state = {
        token: null,
        envelopeId: null,
        fields: [],
        fieldValues: {},
        signaturePad: null,
        activeFieldId: null,
        activeSignatureTab: 'draw' // 'draw', 'type', 'upload'
    };

    // --- DOM ELEMENTS ---
    const viewerContainer = document.getElementById('viewer-container');
    const statusMessage = document.getElementById('status-message');
    const finishBtn = document.getElementById('finish-btn');
    // Signature Modal
    const signatureModal = document.getElementById('signature-modal');
    const signatureCanvas = document.getElementById('signature-canvas');
    const clearSignatureBtn = document.getElementById('clear-signature-btn');
    const saveSignatureBtn = document.getElementById('save-signature-btn');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const typedSignatureInput = document.getElementById('typed-signature-input');
    const typedSignaturePreview = document.getElementById('typed-signature-preview');
    const uploadSignatureInput = document.getElementById('upload-signature-input');
    // Text Modal
    const textModal = document.getElementById('text-modal');
    const textForm = document.getElementById('text-form');
    const textInput = document.getElementById('text-input');
    const cancelButtons = document.querySelectorAll('.cancel-btn');


    // --- INITIALIZATION ---
    async function init() {
        const urlParams = new URLSearchParams(window.location.search);
        state.token = urlParams.get('token');
        if (!state.token) {
            updateStatus('Error: Invalid signing link. No token provided.', 'error');
            return;
        }
        try {
            updateStatus('Loading document...', 'info');
            const data = await getSigningData(state.token);
            state.envelopeId = data.envelope_id;
            state.fields = data.fields;
            
            const firstPage = state.fields.length > 0 ? state.fields[0].page_number : 1;
            await loadPage(firstPage);

            setupSignaturePad();
            setupEventListeners();
        } catch (error) {
            updateStatus(`Error: ${error.message}`, 'error');
        }
    }

    async function loadPage(pageNum) {
        // ... (this function is unchanged)
        try {
            const imageBlob = await getPagePreview(state.envelopeId, pageNum);
            const imageUrl = URL.createObjectURL(imageBlob);
            viewerContainer.innerHTML = `<img src="${imageUrl}" id="pdf-page-image" alt="PDF Page ${pageNum}">`;
            renderFieldsForPage(pageNum);
            updateStatus('');
        } catch (error) {
            updateStatus(`Error loading page: ${error.message}`, 'error');
        }
    }
    
    // --- UI RENDERING ---
    function renderFieldsForPage(pageNum) {
        // ... (this function is mostly unchanged)
        const fieldsForPage = state.fields.filter(f => f.page_number === pageNum);

        fieldsForPage.forEach(field => {
            const fieldEl = document.createElement('div');
            fieldEl.className = 'interactive-field';
            fieldEl.dataset.fieldId = field.id;
            fieldEl.dataset.fieldType = field.type;
            fieldEl.style.left = `${field.x_coord}%`;
            fieldEl.style.top = `${field.y_coord}%`;
            fieldEl.style.width = `${field.width}%`;
            fieldEl.style.height = `${field.height}%`;
            
            const value = state.fieldValues[field.id];
            if(value) {
                fieldEl.classList.add('completed');
                if (field.type === 'signature' || field.type === 'initial') {
                    fieldEl.innerHTML = `<img src="${value}" class="signature-preview">`;
                } else {
                    fieldEl.textContent = value;
                }
            } else {
                fieldEl.textContent = `Click to ${field.type}`;
            }
            viewerContainer.appendChild(fieldEl);
        });
    }

    // ... (updateFinishButton and updateStatus are unchanged)
    function updateFinishButton() {
        const allFieldsCompleted = state.fields.every(field => !!state.fieldValues[field.id]);
        finishBtn.disabled = !allFieldsCompleted;
    }
    function updateStatus(message, type = '') {
        statusMessage.textContent = message;
        statusMessage.className = `status ${type}`;
    }

    // --- SIGNATURE PAD ---
    function setupSignaturePad() {
        // ... (this function is unchanged)
        const canvasContainer = document.querySelector('.signature-pad-container');
        signatureCanvas.width = canvasContainer.offsetWidth;
        signatureCanvas.height = canvasContainer.offsetHeight;
        state.signaturePad = new SignaturePad(signatureCanvas, {
            backgroundColor: 'rgb(255, 255, 255)'
        });
    }

    // --- EVENT LISTENERS ---
    function setupEventListeners() {
        viewerContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('interactive-field')) {
                handleFieldClick(e.target);
            }
        });
        
        // Modal cancel buttons
        cancelButtons.forEach(btn => btn.addEventListener('click', () => {
            signatureModal.style.display = 'none';
            textModal.style.display = 'none';
        }));

        // Text Modal
        textForm.addEventListener('submit', handleSaveText);

        // Signature Modal
        tabButtons.forEach(btn => btn.addEventListener('click', handleTabClick));
        typedSignatureInput.addEventListener('input', (e) => {
            typedSignaturePreview.textContent = e.target.value;
        });
        clearSignatureBtn.addEventListener('click', () => {
            if (state.activeSignatureTab === 'draw') state.signaturePad.clear();
            if (state.activeSignatureTab === 'type') {
                typedSignatureInput.value = '';
                typedSignaturePreview.textContent = '';
            }
        });
        saveSignatureBtn.addEventListener('click', handleSaveSignature);
        finishBtn.addEventListener('click', handleSubmit);
    }

    // --- HANDLERS ---
    function handleFieldClick(fieldEl) {
        const fieldId = parseInt(fieldEl.dataset.fieldId, 10);
        const fieldType = fieldEl.dataset.fieldType;
        state.activeFieldId = fieldId;
        
        if (fieldType === 'signature' || fieldType === 'initial') {
            state.signaturePad.clear();
            signatureModal.style.display = 'flex';
        } else if (fieldType === 'date') {
            const today = new Date().toISOString().split('T')[0];
            state.fieldValues[fieldId] = today;
            fieldEl.textContent = today;
            fieldEl.classList.add('completed');
            updateFinishButton();
        } else if (fieldType === 'text') {
            textInput.value = state.fieldValues[fieldId] || '';
            textModal.style.display = 'flex';
        }
    }

    function handleSaveText(e) {
        e.preventDefault();
        const value = textInput.value;
        if (!value) return;
        
        state.fieldValues[state.activeFieldId] = value;
        const fieldEl = viewerContainer.querySelector(`[data-field-id='${state.activeFieldId}']`);
        fieldEl.textContent = value;
        fieldEl.classList.add('completed');
        
        textModal.style.display = 'none';
        updateFinishButton();
    }

    function handleTabClick(e) {
        const tabId = e.target.dataset.tab;
        state.activeSignatureTab = tabId;

        // Update button UI
        tabButtons.forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
        
        // Update content UI
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
    }

    function handleSaveSignature() {
        let dataUrl;
        switch (state.activeSignatureTab) {
            case 'draw':
                if (state.signaturePad.isEmpty()) {
                    alert("Please provide a signature first.");
                    return;
                }
                dataUrl = state.signaturePad.toDataURL('image/png');
                break;
            case 'type':
                const text = typedSignatureInput.value;
                if (!text) {
                    alert("Please type your name.");
                    return;
                }
                // Convert text to a signature image using canvas
                const tempCanvas = document.createElement('canvas');
                const ctx = tempCanvas.getContext('2d');
                ctx.font = "50px 'Dancing Script', cursive";
                tempCanvas.width = ctx.measureText(text).width + 40;
                tempCanvas.height = 80;
                ctx.font = "50px 'Dancing Script', cursive";
                ctx.fillStyle = "#000";
                ctx.fillText(text, 20, 50);
                dataUrl = tempCanvas.toDataURL('image/png');
                break;
            case 'upload':
                const file = uploadSignatureInput.files[0];
                if (!file) {
                    alert("Please select an image file.");
                    return;
                }
                // Read file as a data URL
                const reader = new FileReader();
                reader.onloadend = () => {
                    saveAndRenderSignature(reader.result);
                };
                reader.readAsDataURL(file);
                return; // Exit because this is async
        }
        
        saveAndRenderSignature(dataUrl);
    }
    
    function saveAndRenderSignature(dataUrl) {
        state.fieldValues[state.activeFieldId] = dataUrl;
        
        const fieldEl = viewerContainer.querySelector(`[data-field-id='${state.activeFieldId}']`);
        fieldEl.innerHTML = `<img src="${dataUrl}" class="signature-preview">`;
        fieldEl.classList.add('completed');

        signatureModal.style.display = 'none';
        updateFinishButton();
    }
    
    async function handleSubmit() {
        // ... (this function is unchanged)
        updateStatus('Submitting your document...', 'info');
        finishBtn.disabled = true;
        const submissionData = {
            fields: Object.keys(state.fieldValues).map(fieldId => ({
                id: parseInt(fieldId, 10),
                value: state.fieldValues[fieldId]
            }))
        };
        try {
            const result = await submitSignature(state.token, submissionData);
            updateStatus(result.message, 'success');
            viewerContainer.innerHTML = `<h2>Thank You!</h2><p>The signing process is complete. You can now close this window.</p>`;
            finishBtn.style.display = 'none';
        } catch (error) {
            updateStatus(`Error: ${error.message}`, 'error');
            finishBtn.disabled = false;
        }
    }
    
    init();
});