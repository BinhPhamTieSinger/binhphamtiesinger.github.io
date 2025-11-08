document.addEventListener('DOMContentLoaded', () => {
    const uploadTrigger = document.getElementById('upload-avatar-trigger');
    const fileInput = document.getElementById('avatar-upload-input');
    const profileAvatar = document.getElementById('profile-main-avatar');
    const profileCard = document.querySelector('.profile-card');

    function showToast(message, timeout = 3000) {
        const t = document.createElement('div');
        t.className = 'toast';
        t.textContent = message;
        document.body.appendChild(t);
        // Force reflow to allow transition
        requestAnimationFrame(() => t.classList.add('show'));
        setTimeout(() => {
            t.classList.remove('show');
            setTimeout(() => t.remove(), 250);
        }, timeout);
    }

    function createUploadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'uploading-overlay';
        overlay.innerHTML = '<div class="uploading-spinner" aria-hidden="true"></div>';
        return overlay;
    }

    uploadTrigger?.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput?.addEventListener('change', async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            showToast('Only image files are allowed.');
            fileInput.value = '';
            return;
        }

        // Preview locally
        const previewUrl = URL.createObjectURL(file);
        profileAvatar.classList.add('previewing');
        const previousSrc = profileAvatar.src;
        profileAvatar.src = previewUrl;

        // Prepare upload
        const formData = new FormData();
        formData.append('avatar', file);

        // Show uploading overlay
        const overlay = createUploadingOverlay();
        profileCard.appendChild(overlay);
        uploadTrigger.disabled = true;

        try {
            const resp = await fetch('/profile/upload-avatar', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            // If server redirected, fetch follows redirects; use final URL if redirected
            if (resp.redirected) {
                window.location.href = resp.url;
                return;
            }

            if (resp.ok) {
                // Best effort: reload to ensure cached avatar is refreshed
                // Bust cache by appending timestamp
                const avatarImgs = document.querySelectorAll(`img[src*="/static/assets/avatars/"]`);
                avatarImgs.forEach(img => {
                    const src = img.getAttribute('src').split('?')[0];
                    img.setAttribute('src', `${src}?v=${Date.now()}`);
                });
                showToast('Avatar uploaded.');
                // Clean up preview class
                profileAvatar.classList.remove('previewing');
            } else {
                // revert preview
                profileAvatar.src = previousSrc;
                showToast('Upload failed. Please try again.');
            }
        } catch (err) {
            profileAvatar.src = previousSrc;
            console.error('Upload error:', err);
            showToast('Upload error. Check console.');
        } finally {
            uploadTrigger.disabled = false;
            overlay.remove();
            fileInput.value = '';
            // release object URL
            URL.revokeObjectURL(previewUrl);
        }
    });

    // Edit profile toggle behaviour
    const editToggle = document.getElementById('edit-profile-toggle');
    const editForm = document.getElementById('profile-edit-form');
    const editCancel = document.getElementById('edit-cancel');

    if (editToggle && editForm) {
        editToggle.addEventListener('click', () => {
            editForm.classList.toggle('hidden');
            // If showing, focus first input
            if (!editForm.classList.contains('hidden')) {
                document.getElementById('edit-username')?.focus();
            }
        });
    }

    editCancel?.addEventListener('click', () => {
        editForm.classList.add('hidden');
    });

    // Optional: client-side simple validation before submit
    editForm?.addEventListener('submit', (e) => {
        const u = document.getElementById('edit-username').value.trim();
        const em = document.getElementById('edit-email').value.trim();
        if (!u || !em) {
            e.preventDefault();
            // show simple inline error
            let err = document.getElementById('profile-error');
            if (!err) {
                err = document.createElement('p');
                err.id = 'profile-error';
                err.className = 'error-message';
                editForm.parentNode.insertBefore(err, editForm);
            }
            err.textContent = 'Username and email cannot be empty.';
            return false;
        }
        // allow server to enforce uniqueness
        return true;
    });
});