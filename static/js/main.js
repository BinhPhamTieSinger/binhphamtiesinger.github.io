document.addEventListener('DOMContentLoaded', () => {
    
    const introLayer = document.getElementById('intro-layer');
    const stageLogo = document.getElementById('intro-logo');
    const stageGreeting = document.getElementById('intro-greeting');
    const mainApp = document.getElementById('main-app');

    // --- 1. INTRO ANIMATION ---
    const introShown = sessionStorage.getItem('introShown');

    if (introShown) {
        if(introLayer) introLayer.style.display = 'none';
        if(mainApp) {
            mainApp.classList.remove('hidden');
            mainApp.style.opacity = '1';
        }
        startTypingEffect();
    } else {
        runIntroAnimation();
    }

    function runIntroAnimation() {
        if(!introLayer) return;
        setTimeout(() => {
            stageLogo.classList.add('fade-out');
            setTimeout(() => {
                stageLogo.classList.add('hidden');
                stageGreeting.classList.remove('hidden');
                stageGreeting.classList.add('fade-in');
                setTimeout(() => {
                    stageGreeting.classList.remove('fade-in');
                    stageGreeting.classList.add('fade-out');
                    setTimeout(() => {
                        introLayer.classList.add('fade-out');
                        setTimeout(() => {
                            introLayer.style.display = 'none';
                            mainApp.classList.remove('hidden');
                            mainApp.classList.add('fade-in');
                            sessionStorage.setItem('introShown', 'true');
                            startTypingEffect();
                        }, 1000);
                    }, 1000);
                }, 3000); 
            }, 1000); 
        }, 3000);
    }

    // --- 2. SCROLL ---
    window.onscroll = function() {
        const header = document.getElementById("myHeader");
        if (header && window.pageYOffset > 50) { 
            header.classList.add("scrolled");
        } else if (header) {
            header.classList.remove("scrolled");
        }
    };

    // --- 3. TYPING ---
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

    // --- 4. CONTACT FORM (FORMSPREE) ---
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = contactForm.querySelector('button');
            const originalText = btn.innerText;
            btn.innerText = "Sending...";
            btn.disabled = true;

            const formData = new FormData(contactForm);

            // REPLACE 'YOUR_FORMSPREE_ID' WITH YOUR ACTUAL ID (e.g., xzyqoprk)
            try {
                const response = await fetch("https://formspree.io/f/movbpyzb", {
                    method: "POST",
                    body: formData,
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    alert("Message sent successfully!");
                    contactForm.reset();
                } else {
                    alert("Oops! There was a problem sending your form.");
                }
            } catch (error) {
                alert("Error connecting to email service.");
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }
});