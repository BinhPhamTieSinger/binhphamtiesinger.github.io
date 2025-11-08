// static/js/project_detail.js

document.addEventListener('DOMContentLoaded', () => {
    // Configure marked with proper options
    marked.setOptions({
        breaks: true,        // Enable line breaks
        gfm: true,          // Enable GitHub Flavored Markdown
        sanitize: false,    // Allow HTML
        headerIds: true,    // Enable header IDs
        mangle: false,      // Don't mangle header IDs
        smartLists: true,   // Enable smart lists
        smartypants: true,  // Enable smart punctuation
        xhtml: true         // Enable XHTML output
    });

    // --- Variable Declarations ---
    const projectFullDescriptionDiv = document.getElementById('projectFullDescription');
    
    // Handle the project description rendering
    if (projectFullDescriptionDiv) {
        const rawDescription = projectFullDescriptionDiv.textContent.trim();
        if (rawDescription) {
            // First unescape any HTML entities
            const unescapedText = rawDescription
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&#x27;/g, "'")
                .replace(/&quot;/g, '"');
            
            // Then parse markdown and render
            projectFullDescriptionDiv.innerHTML = marked.parse(unescapedText);
        }
    }

    // --- Global Markdown Configuration ---
    // Configure marked to use breaks and allow HTML
    marked.setOptions({
        breaks: true,
        sanitize: false // Allows HTML like <font>
    });

    // --- Variable Declarations ---
    const projectId = document.querySelector('.hero-banner-small p')?.getAttribute('data-project-id') || null;

    // Admin buttons
    const editProjectBtn = document.getElementById('editProjectBtn');
    const deleteProjectBtn = document.getElementById('deleteProjectBtn');

    // Admin Add/Edit Project Modal
    const adminProjectModal = document.getElementById('adminProjectModal');
    const closeAdminModalButtons = adminProjectModal.querySelectorAll('.close-button, .cancel-button');
    const adminProjectForm = document.getElementById('adminProjectForm');
    const adminModalTitle = document.getElementById('adminModalTitle');
    const adminProjectIdInput = document.getElementById('adminProjectId');
    const saveProjectBtn = document.getElementById('saveProjectBtn');

    // Form fields for admin modal
    const projectTitleInput = document.getElementById('projectTitle');
    const projectTypeSelect = document.getElementById('projectType');
    const projectDescriptionTextarea = document.getElementById('projectDescription');
    const projectDescriptionPreview = document.getElementById('projectDescriptionPreview');
    const projectShortDescriptionTextarea = document.getElementById('projectShortDescription');
    const projectImageInput = document.getElementById('projectImage');

    // Preview elements for the *card* in admin modal
    const previewCardImage = document.getElementById('previewCardImage');
    const previewCardTitle = document.getElementById('previewCardTitle');
    const previewCardDate = document.getElementById('previewCardDate');
    const previewCardShortDescription = document.getElementById('previewCardShortDescription');

    // Comments & Reactions
    const commentsSection = document.getElementById('commentsSection');
    const reactionsSection = document.getElementById('reactionsSection');
    const loginPrompt = document.querySelector('.login-prompt');
    
    // NEW: Comment Form elements
    const newCommentFormContainer = document.getElementById('newCommentFormContainer'); // Container for moving
    const commentForm = document.getElementById('commentForm');
    const newCommentTextarea = commentForm ? commentForm.querySelector('textarea[name="comment_text"]') : null;
    const newCommentPreview = document.getElementById('commentPreview');
    const cancelReplyBtn = document.getElementById('cancelReplyBtn'); // New
    const replyingToNotice = document.getElementById('replyingToNotice'); // New
    const originalCommentFormParent = newCommentFormContainer ? newCommentFormContainer.parentElement : null; // Store original location


    const isAdmin = document.body.dataset.isAdmin === 'True';
    const isLoggedIn = !loginPrompt;


    // --- Initial Page Render ---

    // DELETED: on-load markdown rendering for main description.
    // The Jinja2 `| safe` filter in project_detail.html now handles this.
    // This fixes the bug where JS was stripping the <font> tag.

    // DELETED: on-load markdown rendering for existing comments.
    // The Jinja2 `| safe` filter in the macro now handles this.
    
    // MODIFIED: Store raw text in edit textareas
    // We still need to do this for the "Edit" function
    document.querySelectorAll('.comment-text-rendered').forEach(div => {
        // Find the corresponding edit textarea and set its value and default value
        const textarea = div.closest('.comment-body').querySelector('.comment-edit-textarea');
        if (textarea) {
            // textarea.value is set by Jinja {{ comment.text }}
            // We just need to set defaultValue for resetting on cancel
            textarea.defaultValue = textarea.value;
        }
    });


    // --- Admin Actions (Edit/Delete) ---
    if (isAdmin) {
        if (editProjectBtn) {
            editProjectBtn.addEventListener('click', () => openAdminProjectModal('edit', projectId));
        }
        if (deleteProjectBtn) {
            deleteProjectBtn.addEventListener('click', () => deleteProject(projectId));
        }
    }

    async function openAdminProjectModal(mode, projectIdToEdit = null) {
        adminProjectForm.reset();
        adminProjectIdInput.value = '';
        previewCardImage.style.display = 'none';
        
        // MODIFIED: Hide preview and reset button text
        if (projectDescriptionPreview) {
            projectDescriptionPreview.style.display = 'none';
            const previewBtn = document.querySelector('.btn-toggle-preview[data-preview-target="projectDescriptionPreview"]');
            if (previewBtn) previewBtn.textContent = 'Show Preview';
        }

        if (mode === 'add') {
            adminModalTitle.textContent = 'Add New Project';
            saveProjectBtn.textContent = 'Create Project';
            previewCardDate.textContent = new Date().toISOString().slice(0, 10);
            updateProjectCardPreview();
        } else if (mode === 'edit' && projectIdToEdit !== null) {
            adminModalTitle.textContent = 'Edit Project';
            saveProjectBtn.textContent = 'Update Project';

            try {
                const response = await fetch(`/api/project/${projectIdToEdit}`);
                if (!response.ok) throw new Error('Failed to fetch project for editing');
                const project = await response.json();

                adminProjectIdInput.value = project.id;
                projectTitleInput.value = project.title;
                projectTypeSelect.value = project.type;
                projectDescriptionTextarea.value = project.description;
                projectShortDescriptionTextarea.value = project.short_description;
                projectImageInput.value = project.image_url;
                previewCardDate.textContent = project.date;
                
                updateProjectCardPreview();
                // Update preview content (it's hidden, but ready)
                if (projectDescriptionPreview) {
                    projectDescriptionPreview.innerHTML = marked.parse(project.description);
                }
            } catch (error) {
                console.error("Error fetching project for edit:", error);
                alert("Failed to load project details for editing.");
                return;
            }
        }
        adminProjectModal.style.display = 'flex';
    }

    function updateProjectCardPreview() {
        previewCardTitle.textContent = projectTitleInput.value || 'Project Title';
        previewCardShortDescription.textContent = projectShortDescriptionTextarea.value || 'Short description for the project card...';

        if (projectImageInput.value) {
            previewCardImage.src = projectImageInput.value;
            previewCardImage.style.display = 'block';
        } else {
            previewCardImage.src = '';
            previewCardImage.style.display = 'none';
        }
    }

    // Event listeners for preview updates in admin modal
    projectTitleInput.addEventListener('input', updateProjectCardPreview);
    projectShortDescriptionTextarea.addEventListener('input', updateProjectCardPreview);
    projectImageInput.addEventListener('input', updateProjectCardPreview);
    
    // MODIFIED: Live Markdown Preview for Project Description (updates hidden preview)
    if (projectDescriptionTextarea && projectDescriptionPreview) {
        projectDescriptionTextarea.addEventListener('input', () => {
            projectDescriptionPreview.innerHTML = marked.parse(projectDescriptionTextarea.value);
        });
    }

    adminProjectForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const id = adminProjectIdInput.value ? parseInt(adminProjectIdInput.value) : null;
        const title = projectTitleInput.value.trim();
        const type = projectTypeSelect.value;
        const description = projectDescriptionTextarea.value; // Don't trim, keep markdown formatting
        const short_description = projectShortDescriptionTextarea.value.trim();
        const image_url = projectImageInput.value.trim() || null;

        if (!title || !description || !short_description) {
            alert('Please fill in all required fields (Title, Description, Short Description).');
            return;
        }

        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('short_description', short_description);
        formData.append('type', type);
        if (image_url) formData.append('image_url', image_url);

        const headers = {
            'X-Requested-With': 'XMLHttpRequest'
        };

        try {
            let response;
            if (id) {
                response = await fetch(`/api/projects/${id}`, {
                    method: 'PUT',
                    headers: headers,
                    body: formData
                });
            } else {
                response = await fetch('/api/projects', {
                    method: 'POST',
                    body: formData
                });
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            alert(`Project ${id ? 'updated' : 'created'} successfully! The page will now refresh.`);
            adminProjectModal.style.display = 'none';
            window.location.reload();
        } catch (error) {
            console.error(`Error ${id ? 'updating' : 'creating'} project:`, error);
            alert(`Failed to ${id ? 'update' : 'create'} project: ${error.message}`);
        }
    });

    async function deleteProject(projectIdToDelete) {
        if (confirm('Are you sure you want to delete this project? This cannot be undone.')) {
            try {
                const response = await fetch(`/api/projects/${projectIdToDelete}`, {
                    method: 'DELETE',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                alert('Project deleted successfully! You will now be redirected to the projects list.');
                window.location.href = '/projects';
            } catch (error) {
                console.error('Error deleting project:', error);
                alert(`Failed to delete project: ${error.message}`);
            }
        }
    }

    // --- User Actions (Comments & Reactions) ---

    // NEW: Toggleable Preview Button Handler
    document.addEventListener('click', (event) => {
        const target = event.target.closest('.btn-toggle-preview');
        if (!target) return;

        const previewTargetId = target.dataset.previewTarget;
        const previewEl = document.getElementById(previewTargetId);
        if (!previewEl) return;

        const isVisible = previewEl.style.display === 'block';
        previewEl.style.display = isVisible ? 'none' : 'block';
        target.textContent = isVisible ? 'Show Preview' : 'Hide Preview';
    });


    // MODIFIED: Live Markdown Preview for New Comment (updates hidden preview)
    if (newCommentTextarea && newCommentPreview) {
        newCommentTextarea.addEventListener('input', () => {
            newCommentPreview.innerHTML = marked.parse(newCommentTextarea.value);
        });
    }

    // Handle new comment submission
    if (commentForm) {
        commentForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const commentText = newCommentTextarea.value.trim();

            if (!commentText) {
                alert('Comment cannot be empty.');
                return;
            }

            const formData = new FormData();
            formData.append('comment_text', commentText);

            // NEW: Add parent_id if it exists
            const parentId = commentForm.dataset.parentId;
            if (parentId) {
                formData.append('parent_id', parentId);
            }

            try {
                const response = await fetch(`/api/project/${projectId}/comments`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }
                
                alert('Comment posted successfully! Refreshing...');
                window.location.reload();
            } catch (error) {
                console.error('Error posting comment:', error);
                alert(`Failed to post comment: ${error.message}`);
            }
        });
    }

    // NEW: Handle "Cancel Reply"
    if (cancelReplyBtn) {
        cancelReplyBtn.addEventListener('click', () => {
            // Move form back to original container
            if (originalCommentFormParent) {
                originalCommentFormParent.appendChild(newCommentFormContainer);
            }
            // Reset form state
            newCommentTextarea.value = '';
            if (newCommentPreview) newCommentPreview.innerHTML = '';
            commentForm.removeAttribute('data-parent-id');
            replyingToNotice.style.display = 'none';
            cancelReplyBtn.style.display = 'none';
        });
    }


    // MODIFIED: Handle Comment Edit/Delete/Save/Cancel/Reply Clicks
    if (commentsSection) {
        commentsSection.addEventListener('click', async (event) => {
            const target = event.target.closest('button');
            if (!target) return;

            const commentContainer = target.closest('.comment-item');
            if (!commentContainer) return;

            const commentId = commentContainer.dataset.commentContainerId;

            // --- NEW: Reply Button ---
            if (target.classList.contains('btn-reply-comment')) {
                const authorUsername = commentContainer.querySelector('.comment-author').dataset.username;
                const replyFormContainer = commentContainer.querySelector('.comment-reply-form-container');
                
                // Move the main comment form
                if (replyFormContainer) {
                    replyFormContainer.appendChild(newCommentFormContainer);
                }
                
                // Set form state
                commentForm.dataset.parentId = commentId;
                newCommentTextarea.value = `@${authorUsername} `;
                newCommentTextarea.focus();
                
                replyingToNotice.textContent = `Replying to @${authorUsername}`;
                replyingToNotice.style.display = 'block';
                cancelReplyBtn.style.display = 'inline-block';
            }
            // --- Edit Button ---
            else if (target.classList.contains('btn-edit-comment')) {
                commentContainer.querySelector('.comment-text-rendered').style.display = 'none';
                commentContainer.querySelector('.comment-edit-form').style.display = 'block';
                // Textarea value is already set by Jinja, just focus
                commentContainer.querySelector('.comment-edit-textarea').focus();
            }
            // --- Cancel Edit Button ---
            else if (target.classList.contains('btn-cancel-edit')) {
                commentContainer.querySelector('.comment-text-rendered').style.display = 'block';
                commentContainer.querySelector('.comment-edit-form').style.display = 'none';
                // Reset textarea to its original default value
                const textarea = commentContainer.querySelector('.comment-edit-textarea');
                textarea.value = textarea.defaultValue;
            }
            // --- Save Comment Button ---
            else if (target.classList.contains('btn-save-comment')) {
                const textarea = commentContainer.querySelector('.comment-edit-textarea');
                const newText = textarea.value; // Keep whitespace

                if (newText.trim() === '') {
                    alert('Comment cannot be empty.');
                    return;
                }

                const formData = new FormData();
                formData.append('comment_text', newText);

                try {
                    const response = await fetch(`/api/comments/${commentId}`, {
                        method: 'PUT',
                        body: formData
                    });
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                    }
                    
                    // Update UI
                    const renderedDiv = commentContainer.querySelector('.comment-text-rendered');
                    renderedDiv.innerHTML = marked.parse(newText); // Parse the new text
                    renderedDiv.style.display = 'block';
                    // Update textarea default value
                    textarea.value = newText;
                    textarea.defaultValue = newText;
                    // Hide form
                    commentContainer.querySelector('.comment-edit-form').style.display = 'none';
                } catch (error) {
                    console.error('Error saving comment:', error);
                    alert(`Failed to save comment: ${error.message}`);
                }
            }
            // --- Delete Comment Button ---
            else if (target.classList.contains('btn-delete-comment')) {
                if (confirm('Are you sure you want to delete this comment? This may also delete replies.')) {
                    try {
                        const response = await fetch(`/api/comments/${commentId}`, {
                            method: 'DELETE'
                        });
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                        }
                        // Remove comment from UI
                        // This will remove the comment and all its children visually
                        commentContainer.remove();
                    } catch (error) {
                        console.error('Error deleting comment:', error);
                        alert(`Failed to delete comment: ${error.message}`);
                    }
                }
            }
        });
    }

    // Handle reaction clicks
    if (reactionsSection) {
        reactionsSection.querySelectorAll('.reaction-btn').forEach(button => {
            if (!button.disabled) {
                button.addEventListener('click', async () => {
                    const reactionType = button.dataset.reaction;
                    const currentProjectId = button.dataset.projectId;

                    const formData = new FormData();
                    formData.append('reaction_type', reactionType);

                    try {
                        const response = await fetch(`/api/project/${currentProjectId}/reactions`, {
                            method: 'POST',
                            body: formData
                        });

                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                        }
                        window.location.reload();
                    } catch (error) {
                        console.error('Error toggling reaction:', error);
                        alert(`Failed to update reaction: ${error.message}`);
                    }
                });
            }
        });
    }

    // Event Listeners for admin modal
    closeAdminModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            adminProjectModal.style.display = 'none';
        });
    });

    window.addEventListener('click', (event) => {
        if (event.target === adminProjectModal) {
            adminProjectModal.style.display = 'none';
        }
    });
});