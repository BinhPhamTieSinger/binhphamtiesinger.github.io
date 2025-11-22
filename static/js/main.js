document.addEventListener('DOMContentLoaded', () => {
    
    // --- VARIABLES ---
    const introLayer = document.getElementById('intro-layer');
    const stageLogo = document.getElementById('intro-logo');
    const stageGreeting = document.getElementById('intro-greeting');
    const mainApp = document.getElementById('main-app');

    // --- 1. INTRO ANIMATION LOGIC (FIXED) ---
    // Check if user has visited in this session
    const introShown = sessionStorage.getItem('introShown');

    if (introShown) {
        // If already visited, hide intro immediately and show app
        if(introLayer) introLayer.style.display = 'none';
        if(mainApp) {
            mainApp.classList.remove('hidden');
            mainApp.style.opacity = '1';
        }
        startTypingEffect(); // Start typing immediately
    } else {
        // If first time, play animation
        runIntroAnimation();
    }

    function runIntroAnimation() {
        if(!introLayer) return; // Guard clause

        // Logo Animation
        setTimeout(() => {
            stageLogo.classList.add('fade-out');

            setTimeout(() => {
                stageLogo.classList.add('hidden');
                
                // Show Greeting
                stageGreeting.classList.remove('hidden');
                stageGreeting.classList.add('fade-in');

                // Wait, then fade out
                setTimeout(() => {
                    stageGreeting.classList.remove('fade-in');
                    stageGreeting.classList.add('fade-out');

                    // Reveal Main Site
                    setTimeout(() => {
                        introLayer.classList.add('fade-out');
                        
                        setTimeout(() => {
                            introLayer.style.display = 'none';
                            mainApp.classList.remove('hidden');
                            mainApp.classList.add('fade-in');
                            
                            // SET FLAG IN SESSION STORAGE
                            sessionStorage.setItem('introShown', 'true');
                            
                            startTypingEffect();
                        }, 1000);
                    }, 1000);
                }, 3000); 
            }, 1000); 
        }, 3000);
    }

    // --- 2. SCROLL EFFECT ---
    window.onscroll = function() {
        const header = document.getElementById("myHeader");
        if (header && window.pageYOffset > 50) { 
            header.classList.add("scrolled");
        } else if (header) {
            header.classList.remove("scrolled");
        }
    };

    // --- 3. TYPING EFFECT ---
    function startTypingEffect() {
        const typedTextElement = document.getElementById('typed-text');
        if (!typedTextElement) return;

        const words = ["Passionate about Minecraft & Code.", "AI Developer and Web Designer."];
        let wordIndex = 0;
        let charIndex = 0;
        let isDeleting = false;
        
        const typingSpeed = 100; 
        const deletingSpeed = 50; 
        const delayBetweenWords = 2000;

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
        type(); 
    }

    // --- 4. CONTACT FORM EMAIL LOGIC (NEW) ---
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // Stop page reload

            // Get data
            const name = contactForm.querySelector('input[type="text"]').value;
            const email = contactForm.querySelector('input[type="email"]').value;
            const message = contactForm.querySelector('textarea').value;
            const btn = contactForm.querySelector('button');

            // Change button state
            const originalText = btn.innerText;
            btn.innerText = "Sending...";
            btn.disabled = true;

            try {
                const response = await fetch('/send-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, message })
                });

                const result = await response.json();

                if (result.success) {
                    alert("Message sent successfully! I will get back to you soon.");
                    contactForm.reset();
                } else {
                    alert("Failed to send message. Please try again.");
                }
            } catch (error) {
                console.error("Error:", error);
                alert("An error occurred.");
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }
});