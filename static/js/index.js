// static/js/index.js

// Header scroll effect
window.onscroll = function() {
    const header = document.getElementById("myHeader");
    if (window.pageYOffset > 50) { // Adjust scroll threshold as needed
        header.classList.add("scrolled");
    } else {
        header.classList.remove("scrolled");
    }
};

// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.navbar ul li a');

    menuToggle.addEventListener('click', function() {
        navbar.classList.toggle('active');
        menuToggle.classList.toggle('active');
    });

    // Close mobile menu when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (navbar.classList.contains('active')) {
                navbar.classList.remove('active');
                menuToggle.classList.remove('active');
            }
        });
    });

    // Typing effect for banner subtitle
    const typedTextElement = document.getElementById('typed-text');
    const words = ["Passionate about Minecraft & Code.", "AI Developer and Web Designer."];
    let wordIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    const typingSpeed = 100; // milliseconds per character
    const deletingSpeed = 50; // milliseconds per character
    const delayBetweenWords = 1500; // milliseconds

    function type() {
        const currentWord = words[wordIndex];
        if (isDeleting) {
            typedTextElement.textContent = currentWord.substring(0, charIndex - 1);
            charIndex--;
        } else {
            typedTextElement.textContent = currentWord.substring(0, charIndex + 1);
            charIndex++;
        }

        let currentSpeed = isDeleting ? deletingSpeed : typingSpeed;

        if (!isDeleting && charIndex === currentWord.length) {
            currentSpeed = delayBetweenWords;
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            wordIndex = (wordIndex + 1) % words.length;
            currentSpeed = typingSpeed;
        }

        setTimeout(type, currentSpeed);
    }

    type(); // Start the typing animation
});