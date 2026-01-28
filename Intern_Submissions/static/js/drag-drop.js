/**
 * Podcast AI - Drag & Drop File Upload
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('audioInput');
    const form = document.querySelector('form');

    if (!uploadArea || !fileInput) return;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('dragover');
        }, false);
    });

    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);

    // Handle file input change
    fileInput.addEventListener('change', handleFiles, false);

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFiles({ target: { files: files } });
    }

    function handleFiles(e) {
        const files = e.target.files;
        if (files.length > 0) {
            const file = files[0];
            
            // Validate file type
            const validTypes = ['audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/flac', 'audio/ogg'];
            if (!validTypes.includes(file.type)) {
                alert('Please select a valid audio file (MP3, WAV, M4A, FLAC)');
                fileInput.value = '';
                return;
            }

            // Update UI to show selected file
            updateUploadAreaWithFile(file);
        }
    }

    function updateUploadAreaWithFile(file) {
        const fileName = file.name;
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // Size in MB

        uploadArea.innerHTML = `
            <div class="upload-icon">✓</div>
            <p class="main">File Ready: ${fileName}</p>
            <p class="sub">${fileSize} MB</p>
        `;
        uploadArea.style.borderColor = 'var(--secondary)';
        uploadArea.style.background = 'rgba(16, 185, 129, 0.05)';
    }

    // Auto-submit if form has auto-submit data attribute
    if (form && form.dataset.autoSubmit === 'true') {
        form.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                setTimeout(() => {
                    form.submit();
                }, 500);
            }
        });
    }
});
