/**
 * Adarsh ID Cards - Main JavaScript
 * Handles: Slider, Mobile Menu, Typing Effect, AJAX Forms, Phone Slideshow, and Scroll Animations
 */


// ===== 2. Hero Typing Effect (Full-Line with Highlighted Product) =====
function initTypingEffect() {
    const typingEl = document.getElementById('typingLine');
    if (!typingEl) return;

    const lines = [
        { before: 'Professional ', product: 'ID Cards', after: ' for Your School' },
        { before: 'Custom ', product: 'Digital Lanyards', after: ' for Your College' },
        { before: 'Premium ', product: 'Badges', after: ' for Your Institution' },
        { before: 'Elegant ', product: 'Invitation Cards', after: ' for Your Event' },
        { before: 'Official ', product: 'Certificates', after: ' for Your Academy' },
        { before: 'Detailed ', product: 'Marksheets', after: ' for Your School' },
        { before: 'Comprehensive ', product: 'Report Cards', after: ' for Your Institute' },
        { before: 'Creative ', product: 'Diaries', after: ' for Your Students' },
        { before: 'Custom ', product: 'Calendars', after: ' for Your Organization' },
        { before: 'Stunning ', product: 'Brochures', after: ' for Your Business' },
    ];

    let lineIndex = 0;
    let charIndex = 0;
    const TYPE_SPEED = 68;
    const HOLD_SPEED = 1800;

    function esc(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function getFirstLineText(line) {
        return line.before + line.product;
    }

    function getFullText(line) {
        return getFirstLineText(line) + line.after;
    }

    function renderFirstLine(line, charsInFirstLine) {
        const beforeLen = line.before.length;
        const firstLine = getFirstLineText(line);

        if (charsInFirstLine <= beforeLen) {
            return esc(firstLine.substring(0, charsInFirstLine));
        }

        return (
            esc(line.before) +
            '<span class="typing-highlight">' +
            esc(firstLine.substring(beforeLen, charsInFirstLine)) +
            '</span>'
        );
    }

    function renderCursor() {
        return '<span class="typing-cursor typing-cursor-inline" aria-hidden="true"></span>';
    }

    function renderLine(line, charsTyped) {
        const firstLine = getFirstLineText(line);
        const firstLineLen = firstLine.length;

        if (charsTyped <= firstLineLen) {
            return '<span class="typing-line-one">' + renderFirstLine(line, charsTyped) + renderCursor() + '</span>';
        }

        const secondLineChars = charsTyped - firstLineLen;
        const secondLineHtml = esc(line.after.substring(0, secondLineChars));

        return (
            '<span class="typing-line-one">' + renderFirstLine(line, firstLineLen) + '</span>' +
            '<span class="typing-line-two">' + secondLineHtml + renderCursor() + '</span>'
        );
    }

    function type() {
        const currentIndex = lineIndex;
        const currentLine = lines[currentIndex];
        const fullText = getFullText(currentLine);
        let speed = TYPE_SPEED;
        let charsToRender;

        if (charIndex < fullText.length) {
            charIndex += 1;
            charsToRender = charIndex;
        } else {
            // Keep the fully typed sentence visible before switching to the next.
            charsToRender = fullText.length;
            speed = HOLD_SPEED;
            lineIndex = (lineIndex + 1) % lines.length;
            charIndex = 0;
        }

        typingEl.innerHTML = renderLine(currentLine, charsToRender);
        // Apply gradient class based on current line index
        typingEl.className = 'typing-gradient-' + currentIndex;

        setTimeout(type, speed);
    }

    setTimeout(type, 800);
}

// ===== 3. Mobile Menu Toggle =====
function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    const overlay = document.querySelector('.mobile-menu-overlay');
    const closeBtn = document.querySelector('.mobile-menu-close');

    if (!hamburger || !navLinks) return;

    function setMenuState(isOpen) {
        navLinks.classList.toggle('active', isOpen);
        hamburger.classList.toggle('active', isOpen);
        hamburger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        document.body.classList.toggle('mobile-menu-open', isOpen);
        document.documentElement.classList.toggle('mobile-menu-open', isOpen);
        if (overlay) {
            overlay.classList.toggle('active', isOpen);
        }
    }

    function closeMenu() {
        setMenuState(false);
    }

    hamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        setMenuState(!navLinks.classList.contains('active'));
    });

    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            closeMenu();
        });
    });

    if (overlay) {
        overlay.addEventListener('click', closeMenu);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeMenu);
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeMenu();
        }
    });

    document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
            closeMenu();
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 999) {
            closeMenu();
        }
    });
}

// ===== 4. UI Enhancements (Scroll, Observers) =====

function initScrollEffects() {
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal-active');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.bento-card, .work-item, .testimonial-card, .info-box, .download-app-wrapper, .section-title, .contact-wrapper, .trusted-schools, .faq-item, .page-hero, .section-header, .filter-tabs, .rating-card, .gallery-item').forEach(el => {
        el.classList.add('reveal-on-scroll');
        observer.observe(el);
    });
}

function createScrollTopButton() {
    const btn = document.createElement('button');
    btn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    btn.className = 'scroll-top-btn';
    document.body.appendChild(btn);

    window.addEventListener('scroll', () => {
        btn.style.display = window.scrollY > 400 ? 'flex' : 'none';
    });

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Functions removed as they are no longer used in templates:
// initPhoneSlideshow, initQrCode, initAppCtaLink, initLogoSpin


// ===== 10. Interactive Hero Grid (Spotlight Effect) =====
function initHeroGrid() {
    const heroes = document.querySelectorAll('.hero, .page-hero, .download-app-section');
    if (heroes.length === 0) return;

    heroes.forEach(hero => {
        hero.addEventListener('mousemove', (e) => {
            const rect = hero.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const px = (x / rect.width) * 100;
            const py = (y / rect.height) * 100;
            hero.style.setProperty('--mouse-x', `${px}%`);
            hero.style.setProperty('--mouse-y', `${py}%`);

            // Create transient interactive bubbles
            if (Math.random() > 0.88) {
                createHeroBubble(x, y, hero);
            }
        });
        
        // Reset position on mouse leave
        hero.addEventListener('mouseleave', () => {
            hero.style.setProperty('--mouse-x', '50%');
            hero.style.setProperty('--mouse-y', '50%');
        });
    });
}

function createHeroBubble(x, y, container) {
    const bubble = document.createElement('div');
    bubble.className = 'hero-bubble';
    const size = Math.random() * 30 + 10;
    bubble.style.width = `${size}px`;
    bubble.style.height = `${size}px`;
    bubble.style.left = `${x}px`;
    bubble.style.top = `${y}px`;
    
    container.appendChild(bubble);
    
    // Remove after animation completes
    setTimeout(() => bubble.remove(), 1500);
}

// ===== Initialize Everything =====
document.addEventListener('DOMContentLoaded', () => {
    initMobileMenu();
    initTypingEffect();
    initHeroGrid();
    if ('requestIdleCallback' in window) {
        requestIdleCallback(runNonCriticalFeatures, { timeout: 1000 });
    } else {
        setTimeout(runNonCriticalFeatures, 1000);
    }
});

function runNonCriticalFeatures() {
    initScrollEffects();
    createScrollTopButton();
}