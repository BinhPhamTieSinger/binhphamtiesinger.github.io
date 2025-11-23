document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. PROJECT DATA ---
    const projectData = {
        'portfolio': {
            title: 'Portfolio V1',
            category: 'Web Development',
            image: './static/assets/images/avatar.png', // Update path
            description: 'This is my personal portfolio website designed from scratch.',
            tech: ['HTML5', 'CSS3', 'JavaScript', 'GitHub Pages'],
            link: 'https://github.com/binhphamtiesinger' 
        },
        'minecraft': {
            title: 'Hardcore Survival',
            category: 'Minecraft Server',
            image: './static/assets/images/avatar.png', // Update path
            description: 'A heavily customized Spigot server designed for hardcore survival gameplay.',
            tech: ['Java', 'Spigot API', 'MySQL'],
            link: '#'
        },
        'discordbot': {
            title: 'Discord Guard Bot',
            category: 'AI Automation',
            image: './static/assets/images/avatar.png', // Update path
            description: 'An automated moderation bot using OpenAI.',
            tech: ['Python', 'Discord.py', 'OpenAI API'],
            link: '#'
        }
    };

    // --- 2. MODAL LOGIC ---
    const modal = document.getElementById('project-modal');
    if(modal) {
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
                    modalImg.src = data.image;
                    modalTitle.textContent = data.title;
                    modalTag.textContent = data.category;
                    modalDesc.textContent = data.description;
                    modalLink.href = data.link;
                    modalTech.innerHTML = '';
                    data.tech.forEach(tech => {
                        const span = document.createElement('span');
                        span.className = 'tech-badge';
                        span.textContent = tech;
                        modalTech.appendChild(span);
                    });
                    modal.classList.remove('hidden');
                    setTimeout(() => modal.classList.add('show'), 10);
                }
            });
        });

        const hideModal = () => {
            modal.classList.remove('show');
            setTimeout(() => modal.classList.add('hidden'), 300);
        };
        if(closeModal) closeModal.addEventListener('click', hideModal);
        window.addEventListener('click', (e) => {
            if (e.target === modal) hideModal();
        });
    }

    // --- 3. ANIMATION & FILTERS ---
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => card.classList.add('fade-in-up'), index * 150);
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
                    setTimeout(() => card.style.display = 'none', 300);
                }
            });
        });
    });

    // --- 4. VIEW COUNTER (CountAPI) ---
    const viewDisplay = document.getElementById('view-count-number');
    if(viewDisplay) {
        // Change 'tiesinger-portfolio-v1' to a unique name for your site
        const NAMESPACE = 'https://binhphamtiesinger.github.io'; 
        const KEY = 'visits';

        // Check if user already visited this session
        const hasVisited = sessionStorage.getItem('hasVisitedSite');

        if (!hasVisited) {
            // Increment count
            fetch(`https://api.countapi.xyz/hit/${NAMESPACE}/${KEY}`)
                .then(res => res.json())
                .then(data => {
                    viewDisplay.textContent = new Intl.NumberFormat().format(data.value);
                    sessionStorage.setItem('hasVisitedSite', 'true');
                })
                .catch(() => viewDisplay.textContent = "Error");
        } else {
            // Just get count without incrementing
            fetch(`https://api.countapi.xyz/get/${NAMESPACE}/${KEY}`)
                .then(res => res.json())
                .then(data => {
                    viewDisplay.textContent = new Intl.NumberFormat().format(data.value);
                })
                .catch(() => viewDisplay.textContent = "Error");
        }
    }
});