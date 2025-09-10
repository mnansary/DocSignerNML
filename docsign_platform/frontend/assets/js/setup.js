document.addEventListener('DOMContentLoaded', () => {
    // --- STATE MANAGEMENT ---
    const state = {
        envelopeId: null,
        recipients: [], // { email, order, color }
        fields: [],     // { page, type, x, y, width, height, assigneeEmail }
        selectedRecipientEmail: null,
        dragging: {
            active: false,
            type: null,
            startX: 0,
            startY: 0,
            element: null
        },
        // New pager state
        currentPage: 1,
        totalPages: 0
    };

    // --- DOM ELEMENTS ---
    const viewerContainer = document.getElementById('viewer-container');
    const recipientSelect = document.getElementById('recipient-select');
    const addRecipientBtn = document.getElementById('add-recipient-btn');
    const modal = document.getElementById('recipient-modal');
    const recipientForm = document.getElementById('recipient-form');
    const cancelModalBtn = document.getElementById('cancel-modal-btn');
    const fieldsToolbar = document.getElementById('fields-toolbar');
    const fieldButtons = document.querySelectorAll('.field-btn');
    const saveSendBtn = document.getElementById('save-send-btn');
    const statusMessage = document.getElementById('status-message');
    // New pager elements
    const prevPageBtn = document.getElementById('prev-page-btn');
    const nextPageBtn = document.getElementById('next-page-btn');
    const currentPageNumEl = document.getElementById('current-page-num');
    const totalPageNumEl = document.getElementById('total-page-num');


    // --- INITIALIZATION ---
    async function init() {
        const urlParams = new URLSearchParams(window.location.search);
        state.envelopeId = urlParams.get('envelopeId');
        if (!state.envelopeId) {
            updateStatus('Error: No Envelope ID found. Please start over.', 'error');
            return;
        }
        
        setupEventListeners();
        
        try {
            // First, get the total page count using PDF.js
            updateStatus('Analyzing document...', 'info');
            const pdfData = await getOriginalPdf(state.envelopeId);
            // Required for PDF.js
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.10.377/pdf.worker.min.js';
            const pdfDoc = await pdfjsLib.getDocument({ data: pdfData }).promise;
            state.totalPages = pdfDoc.numPages;
            
            // Now load the first page and update UI
            await loadPage(state.currentPage);
            updatePager();
        } catch (error) {
            updateStatus(`Error initializing: ${error.message}`, 'error');
        }
    }

    async function loadPage(pageNum) {
        try {
            updateStatus(`Loading page ${pageNum}...`, 'info');
            const imageBlob = await getPagePreview(state.envelopeId, pageNum);
            const imageUrl = URL.createObjectURL(imageBlob);
            viewerContainer.innerHTML = `<img src="${imageUrl}" id="pdf-page-image" alt="PDF Page ${pageNum}">`;
            state.currentPage = pageNum;
            // After loading the new page, re-render the fields for this page
            renderFields();
            updatePager();
            updateStatus('');
        } catch (error) {
            updateStatus(`Error: ${error.message}`, 'error');
        }
    }

    // --- UI & STATE UPDATES ---
    function updateRecipientUI() {
        // ... (this function remains the same)
        recipientSelect.innerHTML = '';
        if (state.recipients.length === 0) {
            recipientSelect.innerHTML = '<option>Add a recipient to start</option>';
            fieldsToolbar.style.display = 'none';
        } else {
            state.recipients.forEach(rec => {
                const option = document.createElement('option');
                option.value = rec.email;
                option.textContent = rec.email;
                recipientSelect.appendChild(option);
            });
            fieldsToolbar.style.display = 'flex';
            if (!state.selectedRecipientEmail) {
                state.selectedRecipientEmail = state.recipients[0].email;
            }
            recipientSelect.value = state.selectedRecipientEmail;
        }
        saveSendBtn.disabled = state.fields.length === 0;
    }
    
    function renderFields() {
        document.querySelectorAll('.placed-field').forEach(el => el.remove());
        // Filter fields to only show ones for the CURRENT page
        const fieldsForCurrentPage = state.fields.filter(f => f.page === state.currentPage);
        
        fieldsForCurrentPage.forEach(field => {
            const fieldEl = document.createElement('div');
            // We store the original index to allow for future deletion/editing
            fieldEl.dataset.index = state.fields.indexOf(field);
            fieldEl.className = 'placed-field';
            fieldEl.style.left = `${field.x}%`;
            fieldEl.style.top = `${field.y}%`;
            fieldEl.style.width = `${field.width}%`;
            fieldEl.style.height = `${field.height}%`;
            
            const recipient = state.recipients.find(r => r.email === field.assigneeEmail);
            fieldEl.style.borderColor = recipient.color;
            fieldEl.textContent = field.type;
            viewerContainer.appendChild(fieldEl);
        });
        saveSendBtn.disabled = state.fields.length === 0;
    }

    function updatePager() {
        currentPageNumEl.textContent = state.currentPage;
        totalPageNumEl.textContent = state.totalPages;
        prevPageBtn.disabled = state.currentPage <= 1;
        nextPageBtn.disabled = state.currentPage >= state.totalPages;
    }

    function updateStatus(message, type = '') {
        // ... (this function remains the same)
        statusMessage.textContent = message;
        statusMessage.className = `status ${type}`;
    }

    // --- EVENT LISTENERS ---
    function setupEventListeners() {
        // ... (existing listeners for modal, form, select, field buttons)
        addRecipientBtn.addEventListener('click', () => modal.style.display = 'flex');
        cancelModalBtn.addEventListener('click', () => modal.style.display = 'none');
        recipientForm.addEventListener('submit', handleAddRecipient);
        recipientSelect.addEventListener('change', (e) => state.selectedRecipientEmail = e.target.value);
        fieldButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                viewerContainer.style.cursor = 'crosshair';
                state.dragging.type = btn.dataset.type;
            });
        });

        // New pager listeners
        prevPageBtn.addEventListener('click', () => {
            if (state.currentPage > 1) loadPage(state.currentPage - 1);
        });
        nextPageBtn.addEventListener('click', () => {
            if (state.currentPage < state.totalPages) loadPage(state.currentPage + 1);
        });

        viewerContainer.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', handleDrag);
        document.addEventListener('mouseup', endDrag);
        saveSendBtn.addEventListener('click', handleSaveAndSend);
    }

    // --- HANDLERS ---
    function handleAddRecipient(e) {
        // ... (this function remains the same)
        e.preventDefault();
        const email = document.getElementById('recipient-email').value;
        const order = parseInt(document.getElementById('signing-order').value, 10);
        if (state.recipients.some(r => r.email === email)) {
            alert('This recipient email has already been added.');
            return;
        }
        const color = `hsl(${(state.recipients.length * 137.508) % 360}, 50%, 50%)`;
        state.recipients.push({ email, order, color });
        updateRecipientUI();
        recipientForm.reset();
        modal.style.display = 'none';
    }

    async function handleSaveAndSend() {
        // ... (this function remains the same)
        updateStatus('Saving configuration...', 'info');
        saveSendBtn.disabled = true;
        const setupData = {
            recipients: state.recipients.map(({email, order}) => ({email, order})),
            fields: state.fields
        };
        try {
            await setupEnvelope(state.envelopeId, setupData);
            updateStatus('Configuration saved. Sending for signatures...', 'info');
            await sendEnvelope(state.envelopeId);
            updateStatus('Success! The document has been sent for signing.', 'success');
        } catch (error) {
            updateStatus(`Error: ${error.message}`, 'error');
            saveSendBtn.disabled = false;
        }
    }

    // --- DRAG-AND-DROP LOGIC ---
    function endDrag(e) {
        // This function needs to be updated to use the current page number
        if (!state.dragging.active) return;
        state.dragging.active = false;
        viewerContainer.style.cursor = 'default';

        const { width, height } = viewerContainer.getBoundingClientRect();
        const fieldData = {
            // UPDATED: Use the current page from state
            page: state.currentPage,
            type: state.dragging.type,
            assigneeEmail: state.selectedRecipientEmail,
            x: (parseFloat(state.dragging.element.style.left) / width) * 100,
            y: (parseFloat(state.dragging.element.style.top) / height) * 100,
            width: (parseFloat(state.dragging.element.style.width) / width) * 100,
            height: (parseFloat(state.dragging.element.style.height) / height) * 100,
        };
        state.fields.push(fieldData);

        state.dragging.element.remove();
        state.dragging = { active: false, type: null, element: null, startX: 0, startY: 0 };
        
        renderFields();
    }
    
    // The startDrag and handleDrag functions remain the same
    function startDrag(e) {
        if (!state.dragging.type || e.target.id !== 'pdf-page-image') return;
        state.dragging.active = true;
        const rect = viewerContainer.getBoundingClientRect();
        state.dragging.startX = e.clientX - rect.left;
        state.dragging.startY = e.clientY - rect.top;
        state.dragging.element = document.createElement('div');
        state.dragging.element.className = 'dragging-box';
        state.dragging.element.style.left = `${state.dragging.startX}px`;
        state.dragging.element.style.top = `${state.dragging.startY}px`;
        viewerContainer.appendChild(state.dragging.element);
    }
    function handleDrag(e) {
        if (!state.dragging.active) return;
        const rect = viewerContainer.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        const width = Math.abs(currentX - state.dragging.startX);
        const height = Math.abs(currentY - state.dragging.startY);
        const left = Math.min(currentX, state.dragging.startX);
        const top = Math.min(currentY, state.dragging.startY);
        state.dragging.element.style.width = `${width}px`;
        state.dragging.element.style.height = `${height}px`;
        state.dragging.element.style.left = `${left}px`;
        state.dragging.element.style.top = `${top}px`;
    }

    // --- RUN ---
    init();
});