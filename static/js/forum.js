document.addEventListener('DOMContentLoaded', function() {
    // Update the markdown-it configuration at the top
    const md = window.markdownit({
        html: true,
        breaks: true,
        linkify: true,
        typographer: true,
    });

    // Fix indentation by trimming each line
    function normalizeMarkdown(text) {
        return text.split('\n')
            .map(line => line.trim())
            .join('\n')
            .trim();
    }

    // Update the post rendering logic
    function renderMarkdown(element) {
        const raw = element.getAttribute('data-raw') || element.textContent || '';
        if (!raw.trim()) return;

        try {
            // Unescape HTML entities
            const unescapedText = raw
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&#x27;/g, "'")
                .replace(/&quot;/g, '"');

            // Render markdown
            element.innerHTML = md.render(unescapedText);
        } catch (e) {
            console.error('Error parsing markdown:', e);
            element.textContent = raw;
        }
    }

    // Initial render of all posts
    document.querySelectorAll('.post-text').forEach(renderMarkdown);

    // Update preview functionality
    const textarea = document.getElementById('replyText');
    const preview = document.getElementById('replyPreview');
    const previewBtn = document.querySelector('.btn-toggle-preview');

    if (textarea && preview && previewBtn) {
        textarea.addEventListener('input', function() {
            if (preview.style.display !== 'none') {
                const normalizedText = normalizeMarkdown(this.value);
                preview.innerHTML = md.render(normalizedText);
            }
        });
    }

    // Update the edit form to also use markdown
    const editButtons = document.querySelectorAll('.edit-post-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const postId = this.dataset.postId;
            const postContentEl = document.getElementById(`post-content-${postId}`);
            const originalMarkdown = postContentEl.getAttribute('data-raw') || postContentEl.textContent.trim();

            const form = document.createElement('form');
            form.className = 'edit-post-form';
            form.innerHTML = `
                <textarea class="edit-textarea" rows="6">${originalMarkdown}</textarea>
                <div class="edit-actions">
                    <div class="preview-controls">
                        <button type="button" class="btn btn-toggle-preview">Show Preview</button>
                    </div>
                    <div class="edit-buttons">
                        <button type="button" class="btn btn-secondary cancel-edit">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save</button>
                    </div>
                </div>
                <div class="markdown-preview" style="display: none;"></div>
            `;
            postContentEl.replaceWith(form);

            const textarea = form.querySelector('.edit-textarea');
            const preview = form.querySelector('.markdown-preview');
            const previewBtn = form.querySelector('.btn-toggle-preview');

            // Setup live preview
            const updatePreview = () => {
                if (preview.style.display !== 'none') {
                    preview.innerHTML = md.render(textarea.value || '');
                }
            };

            previewBtn.addEventListener('click', () => {
                const isShowing = preview.style.display !== 'none';
                preview.style.display = isShowing ? 'none' : 'block';
                previewBtn.textContent = isShowing ? 'Show Preview' : 'Hide Preview';
                if (!isShowing) {
                    updatePreview();
                }
            });

            textarea.addEventListener('input', updatePreview);

            form.querySelector('.cancel-edit').addEventListener('click', () => {
                form.replaceWith(postContentEl);
            });

            form.addEventListener('submit', async (ev) => {
                ev.preventDefault();
                const newText = textarea.value.trim();
                try {
                    const resp = await fetch(`/forum/post/${postId}/edit`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `post_text=${encodeURIComponent(newText)}`
                    });
                    if (resp.ok) {
                        const newDiv = document.createElement('div');
                        newDiv.className = 'post-text markdown-content';
                        newDiv.id = `post-content-${postId}`;
                        newDiv.setAttribute('data-raw', newText);
                        form.replaceWith(newDiv);
                        renderMarkdown(newDiv);  // Render the markdown
                    } else {
                        const err = await resp.json().catch(()=>({detail:'Failed'}));
                        alert(err.detail || 'Failed to update post');
                    }
                } catch (err) {
                    alert('Error updating post');
                }
            });
        });
    });

    // Update the delete button handler
    const deleteButtons = document.querySelectorAll('.delete-post-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            if (!confirm('Are you sure you want to delete this post?')) return;
            
            const postId = this.dataset.postId;
            try {
                const response = await fetch(`/forum/post/${postId}/delete`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    // Remove the post element from DOM
                    const postElement = document.getElementById(`post-${postId}`);
                    if (postElement) {
                        postElement.remove();
                    }
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Failed to delete post');
                }
            } catch (err) {
                console.error('Error deleting post:', err);
                alert('Error deleting post');
            }
        });
    });

    // --- Create-topic modal logic on forum home ---
    const createForumBtn = document.getElementById('createForumBtn');
    const forumCreateModal = document.getElementById('forumCreateModal');
    const forumCreateForm = document.getElementById('forumCreateForm');
    const cancelCreateForum = document.getElementById('cancelCreateForum');
    const categorySelect = document.getElementById('categorySelect');
    const boardSelect = document.getElementById('boardSelect');
    const contentTextarea = document.getElementById('topicContent');
    const contentPreview = document.getElementById('contentPreview');

    if (createForumBtn && forumCreateModal) {
        createForumBtn.addEventListener('click', () => {
            forumCreateModal.classList.add('active');
            // reset
            if (boardSelect) {
                boardSelect.innerHTML = '<option value="">Please select a category first</option>';
                boardSelect.disabled = true;
            }
            if (categorySelect) categorySelect.value = "";
            if (forumCreateForm) forumCreateForm.reset();
            if (contentPreview) contentPreview.innerHTML = '';
        });
    }

    if (cancelCreateForum) {
        cancelCreateForum.addEventListener('click', () => {
            forumCreateModal.classList.remove('active');
            if (forumCreateForm) forumCreateForm.reset();
        });
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', async () => {
            const categoryId = categorySelect.value;
            boardSelect.disabled = true;
            boardSelect.innerHTML = '<option value="">Loading...</option>';
            if (!categoryId) {
                boardSelect.innerHTML = '<option value="">Please select a category first</option>';
                boardSelect.disabled = true;
                return;
            }
            try {
                const resp = await fetch(`/api/forum/boards/${categoryId}`);
                if (resp.ok) {
                    const boards = await resp.json();
                    boardSelect.innerHTML = boards.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
                    boardSelect.disabled = false;
                } else {
                    boardSelect.innerHTML = '<option value="">Failed to load</option>';
                }
            } catch (err) {
                boardSelect.innerHTML = '<option value="">Failed to load</option>';
            }
        });
    }

    // Modify textarea input handler
    if (contentTextarea && contentPreview) {
        contentTextarea.addEventListener('input', function() {
            if (contentPreview.style.display !== 'none' && typeof marked !== 'undefined') {
                contentPreview.innerHTML = marked.parse(this.value || '');
            }
        });
    }

    if (forumCreateForm) {
        forumCreateForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = new FormData(forumCreateForm);
            
            if (!fd.get('board_id') || !fd.get('title') || !fd.get('content')) {
                alert('Please fill in all required fields.');
                return;
            }

            try {
                const resp = await fetch('/api/forum/create-topic', {
                    method: 'POST',
                    body: fd
                });
                
                if (resp.ok) {
                    const j = await resp.json();
                    window.location.href = `/forum/topic/${j.topic_id}`;
                } else {
                    const j = await resp.json().catch(() => ({ detail: 'Failed' }));
                    alert(j.detail || 'Failed to create topic');
                }
            } catch (err) {
                console.error('Error creating topic:', err);
                alert('Error creating topic');
            }
        });
    }

    // --- For standalone new_topic.html page: live preview ---
    const newTopicTextarea = document.getElementById('post_text');
    const newTopicPreview = document.getElementById('newTopicPreview');
    if (newTopicTextarea && newTopicPreview && typeof marked !== 'undefined') {
        newTopicTextarea.addEventListener('input', () => {
            newTopicPreview.innerHTML = marked.parse(newTopicTextarea.value || '');
        });
        newTopicPreview.innerHTML = marked.parse(newTopicTextarea.value || '');
    }

    // --- Reply preview toggle on topic pages ---
    const replyText = document.getElementById('replyText');
    const replyPreview = document.getElementById('replyPreview');
    // const previewBtn = document.querySelector('.btn-toggle-preview');

    // Fix preview buttons - handle all preview scenarios
    function setupPreview(textareaId, previewId, btnClass) {
        const textarea = document.getElementById(textareaId);
        const preview = document.getElementById(previewId);
        const previewBtn = preview?.parentElement.querySelector(btnClass);

        if (textarea && preview && previewBtn) {
            previewBtn.addEventListener('click', function() {
                const isShowing = preview.style.display !== 'none';
                preview.style.display = isShowing ? 'none' : 'block';
                this.textContent = isShowing ? 'Show Preview' : 'Hide Preview';
                if (!isShowing) {
                    preview.innerHTML = marked.parse(textarea.value || '');
                }
            });

            textarea.addEventListener('input', function() {
                if (preview.style.display !== 'none') {
                    preview.innerHTML = marked.parse(this.value || '');
                }
            });
        }
    }

    // Setup preview for different contexts
    setupPreview('replyText', 'replyPreview', '.btn-toggle-preview');
    setupPreview('post_text', 'newTopicPreview', '.btn-toggle-preview');
    setupPreview('topicContent', 'contentPreview', '.btn-toggle-preview');

    // Delete topic button handler
    const deleteTopicBtn = document.querySelector('.delete-topic-btn');
    if (deleteTopicBtn) {
        deleteTopicBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            if (!confirm('Are you sure you want to delete this entire topic? This cannot be undone.')) return;
            
            const topicId = this.dataset.topicId;
            try {
                const response = await fetch(`/forum/topic/${topicId}/delete`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    window.location.href = '/forum'; // Redirect to forum home
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Failed to delete topic');
                }
            } catch (err) {
                console.error('Error deleting topic:', err);
                alert('Error deleting topic');
            }
        });
    }

    // Add to your DOMContentLoaded event handler
    function setupMentionsAutocomplete(textarea) {
        textarea.addEventListener('input', function(e) {
            const pos = this.selectionStart;
            const text = this.value;
            const lastAt = text.lastIndexOf('@', pos);
            
            if (lastAt !== -1 && (lastAt === 0 || text[lastAt - 1] === ' ')) {
                const partial = text.slice(lastAt + 1, pos);
                if (partial.length > 0) {
                    // Here you would typically show autocomplete suggestions
                    // This would require an API endpoint to search users
                    fetchUserSuggestions(partial);
                }
            }
        });
    }

    // Setup mentions for reply textarea and edit forms
    const replyTextarea = document.getElementById('replyText');
    if (replyTextarea) {
        setupMentionsAutocomplete(replyTextarea);
    }
});