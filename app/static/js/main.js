// Enhanced UI logic (theme, flash, password, progress)
document.addEventListener('DOMContentLoaded', function () {
    // -------------------
    // Theme toggle
    // -------------------
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;

    // Respect saved or OS theme on load
    const savedTheme = localStorage.getItem('theme');
    const osTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const initialTheme = savedTheme || osTheme;
    html.setAttribute('data-theme', initialTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // -------------------
    // Mobile menu toggle
    // -------------------
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');

    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function () {
            navbarMenu.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!navbarMenu.contains(e.target) && !navbarToggle.contains(e.target)) {
                navbarMenu.classList.remove('active');
            }
        });
    }

    // -------------------
    // Close flash messages
    // -------------------
    document.querySelectorAll('.flash-close').forEach(button => {
        button.addEventListener('click', function () {
            const flash = this.closest('.flash');
            if (flash) {
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 300);
            }
        });
    });

    // Auto-close flash after 5 sec
    setTimeout(() => {
        document.querySelectorAll('.flash').forEach(flash => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 300);
        });
    }, 5000);

    // -------------------
    // Password strength meter
    // -------------------
    const passwordInput = document.querySelector('input[name="password"]');
    if (passwordInput) {
        const strengthMeter = document.querySelector('.strength-meter');
        const strengthText = document.querySelector('.strength-text');

        passwordInput.addEventListener('input', function () {
            const password = this.value;
            let strength = 0;

            if (password.length >= 8) strength++;
            if (/[a-z]/.test(password)) strength++;
            if (/[A-Z]/.test(password)) strength++;
            if (/\d/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;

            strengthMeter.className = 'strength-meter';

            if (strength === 0) {
                strengthText.textContent = '';
                return;
            }

            if (strength <= 2) {
                strengthMeter.classList.add('strength-weak');
                strengthText.textContent = 'Weak password';
                strengthText.style.color = 'var(--danger)';
            } else if (strength <= 4) {
                strengthMeter.classList.add('strength-medium');
                strengthText.textContent = 'Medium strength';
                strengthText.style.color = 'var(--warning)';
            } else {
                strengthMeter.classList.add('strength-strong');
                strengthText.textContent = 'Strong password';
                strengthText.style.color = 'var(--success)';
            }
        });
    }

    // -------------------
    // Password visibility toggle
    // -------------------
    document.querySelectorAll('.password-toggle i').forEach(icon => {
        icon.addEventListener('click', function () {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);

            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    });

    // -------------------
    // Animate progress bars
    // -------------------
    document.querySelectorAll('.progress-bar').forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 300);
    });
});