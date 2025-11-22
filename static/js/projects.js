document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. PROJECT DATA STORAGE ---
    const projectData = {
        'portfolio': {
            title: 'Portfolio V1',
            category: 'Web Development',
            image: '/static/assets/images/avatar.png',
            description: 'This is my personal portfolio website designed from scratch using Node.js, Express, and pure CSS. It features a custom view counter, email integration via Nodemailer, and a dark-themed aesthetic inspired by gaming UI. It is fully responsive and optimized for performance.',
            tech: ['Node.js', 'Express', 'HTML5', 'CSS3', 'Nodemailer'],
            link: 'https://github.com/binhphamtiesinger' // Replace with real link
        },
        'minecraft': {
            title: 'Hardcore Survival',
            category: 'Minecraft Server',
            image: '/static/assets/images/avatar.png',
            description: 'A heavily customized Spigot server designed for hardcore survival gameplay. Features include a balanced economy system, custom land claiming plugins, and anti-cheat integration. Optimized for high player counts with minimal lag.',
            tech: ['Java', 'Spigot API', 'MySQL', 'Plugin Dev'],
            link: '#'
        },
        'discordbot': {
            title: 'Discord Guard Bot',
            category: 'AI Automation',
            image: '/static/assets/images/avatar.png',
            description: 'An advanced Discord bot that utilizes OpenAI API to filter toxic messages and moderate community channels automatically. It also includes utility commands for server management and user engagement tracking.',
            tech: ['Python', 'Discord.py', 'OpenAI API', 'MongoDB'],
            link: '#'
        }
    };

    // --- 2. MODAL LOGIC ---
    const modal = document.getElementById('project-modal');
    const closeModal = document.querySelector('.close-modal');
    const modalImg = document.getElementById('modal-img');
    const modalTitle = document.getElementById('modal-title');
    const modalTag = document.getElementById('modal-tag');
    const modalDesc = document.getElementById('modal-desc');
    const modalTech = document.getElementById('modal-tech-stack');
    const modalLink = document.getElementById('modal-link');
    const openBtns = document.querySelectorAll('.open-modal-btn');

    openBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const projectId = btn.getAttribute('data-id');
            const data = projectData[projectId];

            if (data) {
                // Populate Modal
                modalImg.src = data.image;
                modalTitle.textContent = data.title;
                modalTag.textContent = data.category;
                modalDesc.textContent = data.description;
                modalLink.href = data.link;

                // Populate Tech Stack
                modalTech.innerHTML = ''; // Clear old
                data.tech.forEach(tech => {
                    const span = document.createElement('span');
                    span.className = 'tech-badge';
                    span.textContent = tech;
                    modalTech.appendChild(span);
                });

                // Show Modal
                modal.classList.remove('hidden');
                // Small delay to allow display:flex to apply before opacity transition
                setTimeout(() => {
                    modal.classList.add('show');
                }, 10);
            }
        });
    });

    // Close Modal Function
    const hideModal = () => {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300); // Match CSS transition time
    };

    if(closeModal) closeModal.addEventListener('click', hideModal);

    // Click outside to close
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            hideModal();
        }
    });

    // --- 3. ANIMATION & FILTERS (Existing code) ---
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in-up');
        }, index * 150);
    });

    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filterValue = btn.getAttribute('data-filter');

            cards.forEach(card => {
                const category = card.getAttribute('data-category');
                if (filterValue === 'all' || category === filterValue) {
                    card.style.display = 'block';
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 50);
                } else {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        card.style.display = 'none';
                    }, 300);
                }
            });
        });
    });

    // --- 4. FETCH VIEW COUNT (Optional Display) ---
    fetch('/api/views')
        .then(res => res.json())
        .then(data => {
            const viewDisplay = document.getElementById('view-count-number');
            if(viewDisplay) {
                // Adds comma separation (e.g., 1,024)
                viewDisplay.textContent = new Intl.NumberFormat().format(data.count);
            }
        })
        .catch(err => console.error('Error fetching views:', err));
});