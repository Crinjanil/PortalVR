document.addEventListener('DOMContentLoaded', function() {

    // === Theme Toggle ===
    const themeToggle = document.getElementById('themeToggle');
    const savedTheme = localStorage.getItem('theme');

    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        updateThemeIcon(true);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('light-theme');
            const isLight = document.body.classList.contains('light-theme');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
            updateThemeIcon(isLight);
        });
    }

    function updateThemeIcon(isLight) {
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = isLight ? 'fas fa-moon' : 'fas fa-sun';
            }
        }
    }

    // === Navbar Scroll Effect ===
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // === Mobile Nav Toggle ===
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            // Animate hamburger
            const spans = navToggle.querySelectorAll('span');
            navToggle.classList.toggle('open');
        });

        // Close menu on link click
        navMenu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
            });
        });
    }

    // === Counter Animation ===
    const counters = document.querySelectorAll('[data-count]');
    if (counters.length > 0) {
        const observerOptions = {
            threshold: 0.5
        };

        const counterObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-count'));
                    animateCounter(el, target);
                    counterObserver.unobserve(el);
                }
            });
        }, observerOptions);

        counters.forEach(counter => counterObserver.observe(counter));
    }

    function animateCounter(el, target) {
        let current = 0;
        const increment = target / 60;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                el.textContent = target;
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(current);
            }
        }, 16);
    }

    // === Game Slider ===
    const sliderTrack = document.getElementById('sliderTrack');
    const sliderPrev = document.getElementById('sliderPrev');
    const sliderNext = document.getElementById('sliderNext');
    const sliderDots = document.getElementById('sliderDots');

    if (sliderTrack) {
        const slides = sliderTrack.querySelectorAll('.slider-slide');
        let currentSlide = 0;
        const totalSlides = slides.length;

        // Create dots
        if (sliderDots) {
            for (let i = 0; i < totalSlides; i++) {
                const dot = document.createElement('div');
                dot.className = 'slider-dot' + (i === 0 ? ' active' : '');
                dot.addEventListener('click', () => goToSlide(i));
                sliderDots.appendChild(dot);
            }
        }

        function goToSlide(index) {
            currentSlide = index;
            sliderTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
            updateDots();
        }

        function updateDots() {
            if (sliderDots) {
                const dots = sliderDots.querySelectorAll('.slider-dot');
                dots.forEach((dot, i) => {
                    dot.classList.toggle('active', i === currentSlide);
                });
            }
        }

        if (sliderPrev) {
            sliderPrev.addEventListener('click', () => {
                currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
                goToSlide(currentSlide);
            });
        }

        if (sliderNext) {
            sliderNext.addEventListener('click', () => {
                currentSlide = (currentSlide + 1) % totalSlides;
                goToSlide(currentSlide);
            });
        }

        // Auto-play
        let autoPlay = setInterval(() => {
            currentSlide = (currentSlide + 1) % totalSlides;
            goToSlide(currentSlide);
        }, 5000);

        // Pause on hover
        const sliderWrapper = sliderTrack.closest('.slider-wrapper');
        if (sliderWrapper) {
            sliderWrapper.addEventListener('mouseenter', () => clearInterval(autoPlay));
            sliderWrapper.addEventListener('mouseleave', () => {
                autoPlay = setInterval(() => {
                    currentSlide = (currentSlide + 1) % totalSlides;
                    goToSlide(currentSlide);
                }, 5000);
            });
        }

        // Touch/swipe support
        let touchStartX = 0;
        let touchEndX = 0;

        sliderTrack.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        sliderTrack.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            const diff = touchStartX - touchEndX;
            if (Math.abs(diff) > 50) {
                if (diff > 0) {
                    currentSlide = (currentSlide + 1) % totalSlides;
                } else {
                    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
                }
                goToSlide(currentSlide);
            }
        }, { passive: true });
    }

    // === Auto-dismiss Messages ===
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        const msgs = messagesContainer.querySelectorAll('.message');
        msgs.forEach(msg => {
            const delay = parseInt(msg.getAttribute('data-auto-dismiss')) || 5000;
            setTimeout(() => {
                msg.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => msg.remove(), 300);
            }, delay);
        });
    }

    // === Hero Particles ===
    const particlesContainer = document.getElementById('particles');
    if (particlesContainer) {
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: ${Math.random() * 3 + 1}px;
                height: ${Math.random() * 3 + 1}px;
                background: rgba(227, 25, 55, ${Math.random() * 0.3 + 0.1});
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: float ${Math.random() * 10 + 10}s linear infinite;
                animation-delay: ${Math.random() * 5}s;
            `;
            particlesContainer.appendChild(particle);
        }

        // Add float animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes float {
                0% { transform: translateY(0) translateX(0); opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { transform: translateY(-100vh) translateX(${Math.random() * 200 - 100}px); opacity: 0; }
            }
            @keyframes slideOut {
                to { transform: translateX(120%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    // === Search form auto-submit ===
    const gameSearchInput = document.getElementById('gameSearchInput');
    if (gameSearchInput) {
        let searchTimeout;
        gameSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                document.getElementById('gamesSearchForm').submit();
            }, 500);
        });
    }

    // === Smooth scroll for anchor links ===
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // === Card hover effects ===
    document.querySelectorAll('.game-card, .about-card, .loyalty-card, .package-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        });
    });
});
