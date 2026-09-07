(function () {
    const basePath = window.APP_BASE_PATH || '';
    const fileInput = document.getElementById('avatar-file');
    const uploadArea = document.getElementById('avatar-upload-area');
    if (!fileInput || !uploadArea) return;

    const cropperWrap = document.getElementById('avatar-cropper-wrap');
    const cropImage = document.getElementById('avatar-crop-image');
    const saveBtn = document.getElementById('avatar-save-btn');
    const cancelBtn = document.getElementById('avatar-cancel-btn');
    const statusEl = document.getElementById('avatar-upload-status');

    let cropper = null;

    function resetPicker() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        cropperWrap.hidden = true;
        fileInput.value = '';
    }

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            cropImage.src = event.target.result;
            cropperWrap.hidden = false;
            if (cropper) cropper.destroy();
            cropper = new Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                background: false,
            });
        };
        reader.readAsDataURL(file);
    });

    cancelBtn.addEventListener('click', resetPicker);

    saveBtn.addEventListener('click', () => {
        if (!cropper) return;

        const canvas = cropper.getCroppedCanvas({ width: 320, height: 320 });
        canvas.toBlob((blob) => {
            const formData = new FormData();
            formData.append('avatar', blob, 'avatar.jpg');
            formData.append('csrf_token', uploadArea.dataset.csrfToken);

            saveBtn.disabled = true;
            statusEl.textContent = 'Sparar...';

            fetch(basePath + '/members/upload_picture.cgi', { method: 'POST', body: formData })
                .then(() => {
                    window.location.href = basePath + '/members/profile.cgi';
                })
                .catch(() => {
                    saveBtn.disabled = false;
                    statusEl.textContent = 'Något gick fel. Försök igen.';
                });
        }, 'image/jpeg', 0.9);
    });
})();
