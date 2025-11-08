// static/js/projects.js

document.addEventListener('DOMContentLoaded', () => {
    const currentProjectsGrid = document.getElementById('currentProjectsGrid');
    const futureProjectsGrid = document.getElementById('futureProjectsGrid');
    const adminProjectModal = document.getElementById('adminProjectModal');
    const closeButtons = adminProjectModal.querySelectorAll('.close-button, .cancel-button'); // Only target modal buttons
    const addProjectBtn = document.getElementById('addProjectBtn');
    const adminProjectForm = document.getElementById('adminProjectForm');
    const saveProjectBtn = document.getElementById('saveProjectBtn');

    // Admin form elements
    const adminModalTitle = document.getElementById('adminModalTitle');
    const adminProjectId = document.getElementById('adminProjectId');
    const projectTitleInput = document.getElementById('projectTitle');
    const projectTypeSelect = document.getElementById('projectType');
    const projectDescriptionTextarea = document.getElementById('projectDescription');
    const projectShortDescriptionTextarea = document.getElementById('projectShortDescription');
    const projectImageInput = document.getElementById('projectImage');

    // Preview elements for the *card* (new)
    const previewCardImage = document.getElementById('previewCardImage');
    const previewCardTitle = document.getElementById('previewCardTitle');
    const previewCardDate = document.getElementById('previewCardDate');
    const previewCardShortDescription = document.getElementById('previewCardShortDescription');

    const isAdmin = document.body.dataset.isAdmin === 'True'; // Get from Jinja context

    // Function to fetch and render projects from the backend API
    async function fetchAndRenderProjects() {
        currentProjectsGrid.innerHTML = `
            <div class="project-card placeholder-card">
                <h4>Loading Current Projects...</h4>
                <p>Please wait.</p>
            </div>`;
        futureProjectsGrid.innerHTML = `
            <div class="project-card placeholder-card">
                <h4>Loading Future Projects...</h4>
                <p>Please wait.</p>
            </div>`;

        try {
            const response = await fetch('/api/projects');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const projects = await response.json();

            currentProjectsGrid.innerHTML = '';
            futureProjectsGrid.innerHTML = '';

            const current = projects.filter(p => p.type === 'current');
            const future = projects.filter(p => p.type === 'future');

            if (current.length === 0) {
                currentProjectsGrid.innerHTML = `
                    <div class="project-card placeholder-card">
                        <h4>No Current Projects Yet</h4>
                        <p>New projects will appear here soon!</p>
                    </div>`;
            } else {
                current.forEach(project => currentProjectsGrid.appendChild(createProjectCard(project)));
            }

            if (future.length === 0) {
                futureProjectsGrid.innerHTML = `
                    <div class="project-card placeholder-card">
                        <h4>No Future Projects Planned</h4>
                        <p>New ideas are always on the horizon!</p>
                    </div>`;
            } else {
                future.forEach(project => futureProjectsGrid.appendChild(createProjectCard(project)));
            }

        } catch (error) {
            console.error('Error fetching projects:', error);
            currentProjectsGrid.innerHTML = `<div class="project-card placeholder-card error-card"><h4>Failed to load projects</h4><p>Please try again later.</p></div>`;
            futureProjectsGrid.innerHTML = `<div class="project-card placeholder-card error-card"><h4>Failed to load projects</h4><p>Please try again later.</p></div>`;
        }
    }

    // Function to create a project card element
    function createProjectCard(project) {
        const card = document.createElement('div');
        card.classList.add('project-card');
        card.setAttribute('data-id', project.id);

        const imageUrl = project.image_url && project.image_url !== 'null' ? project.image_url : '/static/assets/images/default-project.png';

        card.innerHTML = `
            <img src="${imageUrl}" alt="${project.title}">
            <h4>${project.title}</h4>
            <p class="project-date">Created: ${project.date}</p>
            <p class="project-short-desc">${project.short_description}</p>
        `;
        
        // Admin buttons for editing/deleting on the list page
        if (isAdmin) {
            const adminActionsDiv = document.createElement('div');
            adminActionsDiv.classList.add('card-actions');
            adminActionsDiv.innerHTML = `
                <button class="btn btn-small btn-secondary edit-card-btn" data-id="${project.id}">Edit</button>
                <button class="btn btn-small btn-delete delete-card-btn" data-id="${project.id}">Delete</button>
            `;
            card.appendChild(adminActionsDiv);

            adminActionsDiv.querySelector('.edit-card-btn').addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent card click event from firing
                openAdminProjectModal('edit', project.id);
            });
            adminActionsDiv.querySelector('.delete-card-btn').addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent card click event from firing
                deleteProject(project.id);
            });
        }
        
        // Add click listener to the card (excluding action buttons) to navigate to detail page
        card.addEventListener('click', (event) => {
            if (!event.target.closest('.card-actions')) { // Don't navigate if action button is clicked
                window.location.href = `/project/${project.id}`;
            }
        });

        return card;
    }

    // Function to open admin add/edit project modal
    async function openAdminProjectModal(mode, projectId = null) {
        adminProjectForm.reset(); // Clear form
        adminProjectId.value = '';
        previewCardImage.style.display = 'none'; // Hide preview image by default

        if (mode === 'add') {
            adminModalTitle.textContent = 'Add New Project';
            saveProjectBtn.textContent = 'Create Project';
            previewCardDate.textContent = new Date().toISOString().slice(0, 10); // Default to today's date
            updateProjectCardPreview(); // Initialize preview
        } else if (mode === 'edit' && projectId !== null) {
            adminModalTitle.textContent = 'Edit Project';
            saveProjectBtn.textContent = 'Update Project';
            
            try {
                const response = await fetch(`/api/project/${projectId}`); // Fetch full project details
                if (!response.ok) throw new Error('Failed to fetch project for editing');
                const project = await response.json();

                adminProjectId.value = project.id;
                projectTitleInput.value = project.title;
                projectTypeSelect.value = project.type;
                projectDescriptionTextarea.value = project.description;
                projectShortDescriptionTextarea.value = project.short_description;
                projectImageInput.value = project.image_url;
                previewCardDate.textContent = project.date; // Keep original date for card preview
                updateProjectCardPreview(); // Populate and update preview
            } catch (error) {
                console.error("Error fetching project for edit:", error);
                alert("Failed to load project details for editing.");
                return;
            }
        }

        adminProjectModal.style.display = 'flex';
    }

    // Function to update the project card preview (for the admin modal)
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

    // Event listeners for preview updates
    projectTitleInput.addEventListener('input', updateProjectCardPreview);
    projectShortDescriptionTextarea.addEventListener('input', updateProjectCardPreview);
    projectImageInput.addEventListener('input', updateProjectCardPreview);

    // Save/Update Project (Admin Action)
    adminProjectForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const id = adminProjectId.value ? parseInt(adminProjectId.value) : null;
        const title = projectTitleInput.value.trim();
        const type = projectTypeSelect.value;
        const description = projectDescriptionTextarea.value.trim();
        const short_description = projectShortDescriptionTextarea.value.trim();
        const image_url = projectImageInput.value.trim() || null; // Use null if empty

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

        try {
            let response;
            if (id) {
                // Edit existing project
                response = await fetch(`/api/projects/${id}`, {
                    method: 'PUT',
                    body: formData
                });
            } else {
                // Add new project
                response = await fetch('/api/projects', {
                    method: 'POST',
                    body: formData
                });
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            alert(`Project ${id ? 'updated' : 'created'} successfully!`);
            adminProjectModal.style.display = 'none';
            fetchAndRenderProjects(); // Re-fetch and re-render projects
        } catch (error) {
            console.error(`Error ${id ? 'updating' : 'creating'} project:`, error);
            alert(`Failed to ${id ? 'update' : 'create'} project: ${error.message}`);
        }
    });

    // Delete Project (Admin Action)
    async function deleteProject(projectId) {
        if (confirm('Are you sure you want to delete this project? This cannot be undone.')) {
            try {
                const response = await fetch(`/api/projects/${projectId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                alert('Project deleted successfully!');
                fetchAndRenderProjects(); // Re-fetch and re-render projects
            } catch (error) {
                console.error('Error deleting project:', error);
                alert(`Failed to delete project: ${error.message}`);
            }
        }
    }


    // Event Listeners for modals
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            adminProjectModal.style.display = 'none';
        });
    });

    window.addEventListener('click', (event) => {
        if (event.target === adminProjectModal) {
            adminProjectModal.style.display = 'none';
        }
    });

    if (addProjectBtn) { // Only if admin button exists
        addProjectBtn.addEventListener('click', () => openAdminProjectModal('add'));
    }

    // Initial fetch and render of projects
    fetchAndRenderProjects();
});