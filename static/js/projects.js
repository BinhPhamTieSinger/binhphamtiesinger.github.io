// Project Data
const projectsData = {
    'ml-platform': {
        title: 'ML & DL Learning Platform',
        image: '/static/assets/images/projects/ml-platform.png',
        icon: '🧠',
        description: `
            <p>A comprehensive web-based platform designed to democratize Machine Learning and Deep Learning education through interactive tutorials and hands-on coding exercises.</p>
            
            <h3>Key Features:</h3>
            <ul>
                <li>Interactive tutorials with embedded code editors</li>
                <li>Real-time neural network visualizer</li>
                <li>Project gallery with practical examples</li>
                <li>Community forum and progress tracking</li>
            </ul>
            
            <h3>Tech Stack:</h3>
            <p>React, Node.js, TensorFlow.js, Python, Flask, MongoDB</p>
        `,
        link: '#'
    },
    'geometry-parser': {
        title: 'Geometry Problem Parser',
        image: '/static/assets/images/projects/geometry-parser.jpg',
        icon: '📐',
        description: `
            <p>An innovative automation tool that converts textual geometry problems into visual representations using NLP and the GeoGebra Engine.</p>
            
            <h3>Key Features:</h3>
            <ul>
                <li>NLP-powered problem understanding</li>
                <li>Automatic geometric diagram generation</li>
                <li>Step-by-step solution guidance</li>
                <li>Export in multiple formats (SVG, PNG)</li>
            </ul>
            
            <h3>Tech Stack:</h3>
            <p>Python, GeoGebra API, spaCy, NLTK, FastAPI</p>
        `,
        link: '#'
    },
    'ai-chatbot': {
        title: 'AI Agent Chatbot System',
        image: '/static/assets/images/projects/ai-chatbot.jpg',
        icon: '🤖',
        description: `
            <p>A sophisticated AI-powered digital assistant leveraging advanced agents for task management and seamless productivity tool integration.</p>
            
            <h3>Key Features:</h3>
            <ul>
                <li>Multi-agent architecture for specialized tasks</li>
                <li>Email and Google Drive integration</li>
                <li>Task scheduling and calendar management</li>
                <li>Voice interaction support</li>
            </ul>
            
            <h3>Tech Stack:</h3>
            <p>Node.js, OpenAI GPT-4, LangChain, Google APIs, MongoDB</p>
        `,
        link: '#'
    },
    'thetamind': {
        title: 'ThetaMind Math Platform',
        image: '/static/assets/images/projects/thetamind.jpg',
        icon: '📊',
        description: `
            <p>A revolutionary mathematics learning platform combining gamification with adaptive learning algorithms to make math engaging and accessible.</p>
            
            <h3>Key Features:</h3>
            <ul>
                <li>AI-powered adaptive difficulty adjustment</li>
                <li>Gamified challenges with leaderboards</li>
                <li>Interactive visualizations and graphs</li>
                <li>Detailed progress analytics</li>
            </ul>
            
            <h3>Tech Stack:</h3>
            <p>React, Node.js, Express, PostgreSQL, D3.js, Redux</p>
        `,
        link: '#'
    },
    'unity-games': {
        title: 'Unity Game Development',
        image: '/static/assets/images/projects/unity-games.jpg',
        icon: '🎮',
        description: `
            <p>A portfolio of immersive games developed using Unity Engine, showcasing expertise in game mechanics, 3D graphics, and player experience design.</p>
            
            <h3>Featured Games:</h3>
            <ul>
                <li><strong>Cyber Runner:</strong> Fast-paced endless runner</li>
                <li><strong>Puzzle Nexus:</strong> 3D physics-based puzzles</li>
                <li><strong>Space Odyssey:</strong> Top-down space shooter</li>
                <li><strong>Dungeon Quest:</strong> RPG dungeon crawler</li>
            </ul>
            
            <h3>Tech Stack:</h3>
            <p>Unity Engine, C#, Blender, Custom Shaders</p>
        `,
        link: '#'
    }
};

// DOM Elements
const modal = document.getElementById('projectModal');
const modalClose = document.querySelector('.modal-close');
const projectCards = document.querySelectorAll('.project-card');
const modalImage = document.getElementById('modalImage');
const modalImagePlaceholder = document.getElementById('modalImagePlaceholder');

// Open Modal
projectCards.forEach(card => {
    card.addEventListener('click', () => {
        const projectId = card.getAttribute('data-project');
        const project = projectsData[projectId];
        
        if (project) {
            // Update modal content
            document.getElementById('modalTitle').textContent = project.title;
            document.getElementById('modalDescription').innerHTML = project.description;
            document.getElementById('modalLink').href = project.link;
            
            // Try to load image, fallback to icon
            if (project.image) {
                modalImage.src = project.image;
                modalImage.style.display = 'block';
                modalImagePlaceholder.style.display = 'none';
                
                // Handle image load error
                modalImage.onerror = function() {
                    modalImage.style.display = 'none';
                    modalImagePlaceholder.textContent = project.icon;
                    modalImagePlaceholder.style.display = 'flex';
                };
            } else {
                modalImage.style.display = 'none';
                modalImagePlaceholder.textContent = project.icon;
                modalImagePlaceholder.style.display = 'flex';
            }
            
            // Show modal
            modal.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
    });
});

// Close Modal
modalClose.addEventListener('click', closeModal);

modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeModal();
    }
});

function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Escape key to close modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
        closeModal();
    }
});

// Scroll effect for header (reuse from main.js logic)
window.onscroll = function() {
    const header = document.getElementById("myHeader");
    if (header && window.pageYOffset > 50) { 
        header.classList.add("scrolled");
    } else if (header) {
        header.classList.remove("scrolled");
    }
};

// Mobile menu toggle
const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelector('.nav-links');

if(menuToggle) {
    menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('mobile-active');
        menuToggle.classList.toggle('active');
    });

    // Close menu when clicking on a link
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('mobile-active');
            menuToggle.classList.remove('active');
        });
    });
}
