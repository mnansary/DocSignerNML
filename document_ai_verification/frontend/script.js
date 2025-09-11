document.addEventListener('DOMContentLoaded', () => {
    const nsvFileInput = document.getElementById('nsv-file');
    const svFileInput = document.getElementById('sv-file');
    const nsvFileName = document.getElementById('nsv-file-name');
    const svFileName = document.getElementById('sv-file-name');
    const verifyButton = document.getElementById('verify-button');
    const resultsSection = document.getElementById('results-section');
    const pageResultsContainer = document.getElementById('page-results-container');

    function checkFilesAndEnableButton() {
        const nsvReady = nsvFileInput.files.length > 0;
        const svReady = svFileInput.files.length > 0;
        verifyButton.disabled = !(nsvReady && svReady);
    }

    // Update file name display on selection
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

    // Handle verification button click
    verifyButton.addEventListener('click', async () => {
        // Reset UI
        verifyButton.disabled = true;
        verifyButton.textContent = 'Processing... Please Wait';
        resultsSection.classList.add('hidden');
        pageResultsContainer.innerHTML = '';
        
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

            const report = await response.json();
            displayReport(report);

        } catch (error) {
            alert(`An error occurred: ${error.message}`);
            console.error('Verification failed:', error);
        } finally {
            // Re-enable the button once processing is complete
            verifyButton.disabled = false;
            verifyButton.textContent = 'Verify Documents';
        }
    });

    function displayReport(report) {
        // Populate summary
        document.getElementById('overall-status').textContent = report.overall_status;
        document.getElementById('overall-status').className = report.overall_status;
        document.getElementById('nsv-filename').textContent = report.nsv_filename;
        document.getElementById('sv-filename').textContent = report.sv_filename;
        document.getElementById('page-count').textContent = report.page_count;

        // Populate page-wise results
        report.page_results.forEach(page => {
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page-result';
            const statusClass = page.page_status.replace(/\s+/g, '-');
            pageDiv.innerHTML = `
                <div class="page-header">
                    <h3>Page ${page.page_number}</h3>
                    <span class="page-status ${statusClass}">${page.page_status}</span>
                </div>
                <div class="page-content">
                    <h4>Auditor's Findings</h4>
                    <p>${page.findings}</p>
                </div>
            `;
            pageResultsContainer.appendChild(pageDiv);
        });

        // Add event listeners for collapsibles
        document.querySelectorAll('.page-header').forEach(header => {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                content.classList.toggle('open');
            });
        });

        resultsSection.classList.remove('hidden');
    }
});