// Typing effect for the "Hi, I'm Kostas" text
document.addEventListener("DOMContentLoaded", function () {
    const text = "Hi, I'm Thomas Kopalidis";
    let index = 0;
    let speed = 150;
    const textElement = document.getElementById("text");
    const cursorElement = document.querySelector(".cursor");

    function typeEffect() {
        if (index < text.length) {
            textElement.innerHTML += text.charAt(index);
            index++;
            setTimeout(typeEffect, speed);
        }
    }

    typeEffect();
});

// Smooth scrolling for navigation
document.addEventListener("DOMContentLoaded", function () {
    const navLinks = document.querySelectorAll("nav a");

    navLinks.forEach(link => {
        link.addEventListener("click", function (event) {
            const href = this.getAttribute("href");
            if (href.charAt(0) === "#") {
                event.preventDefault();
                const targetId = href.substring(1);
                const targetSection = document.getElementById(targetId);

                if (targetSection) {
                    window.scrollTo({
                        top: targetSection.offsetTop - 60,
                        behavior: "smooth"
                    });
                }
            }
        });
    });
});

// Mobile menu toggle
document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.querySelector(".menu-toggle");
    const mobileMenu = document.querySelector(".mobile-menu");
    menuToggle.addEventListener("click", function () {
        this.classList.toggle("active");
        mobileMenu.classList.toggle("open");
    });
});
