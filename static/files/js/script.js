/* ============================================================
   TABLE OF CONTENTS
   1.  DOM Ready Wrapper
   2.  Slider Initializers
       a. Popular Destinations Slider
       b. Top Packages Slider
   3.  Theme Toggle (Dark Mode) - IMPROVED
   4.  Cookie Popup
   5.  Back to Top
   6.  Smooth Scroll
   7.  Counters
   8.  Reveal Animations (AOS substitute)
   9.  Newsletter Validation
  10.  Navigation
  11.  Reviews Carousel
  12.  Initialization
============================================================ */

(function() {
  'use strict';

  /* ===== 1. DOM Ready Wrapper ===== */
  document.addEventListener('DOMContentLoaded', function() {

    /* ===== 2a. Popular Destinations Slider ===== */
    function initDestinationsSlider() {
      var slider = document.getElementById('destinations-slider');
      if (!slider) return;

      // Only initialize if lightSlider is available and not already initialized
      if (typeof $.fn.lightSlider === 'function' && !slider.classList.contains('lSSlide')) {
        try {
          $(slider).lightSlider({
            item: 3,
            slideMove: 1,
            speed: 600,
            auto: true,
            loop: true,
            pause: 4000,
            pauseOnHover: true,
            controls: true,
            pager: true,
            enableTouch: true,
            enableDrag: true,
            swipeThreshold: 40,
            freeMove: true,
            keyPress: true,
            responsive: [
              {
                breakpoint: 992,
                settings: { item: 2, slideMove: 1 }
              },
              {
                breakpoint: 576,
                settings: { item: 1, slideMove: 1 }
              }
            ],
            onSliderLoad: function() {
              // Lazy loading compatibility: trigger load for images
              var imgs = slider.querySelectorAll('img[data-src]');
              for (var i = 0; i < imgs.length; i++) {
                if (imgs[i].dataset.src) {
                  imgs[i].src = imgs[i].dataset.src;
                  imgs[i].removeAttribute('data-src');
                }
              }
            }
          });
        } catch (e) {
          // Defensive: fallback if lightSlider fails
          console.warn('Destinations slider initialization failed:', e);
        }
      }
    }

    /* ===== 2b. Top Packages Slider ===== */
    function initPackagesSlider() {
      var slider = document.getElementById('packages-slider');
      if (!slider) return;

      if (typeof $.fn.lightSlider === 'function' && !slider.classList.contains('lSSlide')) {
        try {
          $(slider).lightSlider({
            item: 3,
            slideMove: 1,
            speed: 600,
            auto: true,
            loop: true,
            pause: 4500,
            pauseOnHover: true,
            controls: true,
            pager: true,
            enableTouch: true,
            enableDrag: true,
            swipeThreshold: 40,
            freeMove: true,
            keyPress: true,
            responsive: [
              {
                breakpoint: 992,
                settings: { item: 2, slideMove: 1 }
              },
              {
                breakpoint: 576,
                settings: { item: 1, slideMove: 1 }
              }
            ]
          });
        } catch (e) {
          console.warn('Packages slider initialization failed:', e);
        }
      }
    }

    /* ===== 3. Theme Toggle (Dark Mode) - IMPROVED ===== */
    function initThemeToggle() {
      var toggleBtn = document.getElementById('theme-toggle');
      if (!toggleBtn) return;

      var icon = document.getElementById('theme-icon');
      var body = document.body;

      // Check saved preference
      var savedTheme = localStorage.getItem('theme') || 'light';
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

      // Set initial theme
      if (savedTheme === 'dark' || (!localStorage.getItem('theme') && prefersDark)) {
        body.classList.add('dark-mode');
        if (icon) icon.textContent = '☀️';
      } else {
        body.classList.remove('dark-mode');
        if (icon) icon.textContent = '🌙';
      }

      // Toggle on click
      toggleBtn.addEventListener('click', function() {
        var isDark = body.classList.toggle('dark-mode');

        // Update icon
        if (icon) {
          icon.textContent = isDark ? '☀️' : '🌙';
        }

        // Save preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
      });
    }

    /* ===== 4. Cookie Popup ===== */
    function initCookiePopup() {
      var popup = document.getElementById('cookie-popup');
      var acceptBtn = document.getElementById('accept-cookies');
      if (!popup || !acceptBtn) return;

      if (localStorage.getItem('cookiesAccepted') === 'true') {
        popup.style.display = 'none';
        return;
      }

      acceptBtn.addEventListener('click', function() {
        localStorage.setItem('cookiesAccepted', 'true');
        popup.style.display = 'none';
      });
    }

    /* ===== 5. Back to Top ===== */
    function initBackToTop() {
      var btn = document.getElementById('back-to-top');
      if (!btn) return;

      window.addEventListener('scroll', function() {
        if (window.scrollY > 400) {
          btn.classList.add('visible');
        } else {
          btn.classList.remove('visible');
        }
      });

      btn.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    /* ===== 6. Smooth Scroll (for anchor links) ===== */
    function initSmoothScroll() {
      var anchors = document.querySelectorAll('a[href^="#"]');
      for (var i = 0; i < anchors.length; i++) {
        anchors[i].addEventListener('click', function(e) {
          var targetId = this.getAttribute('href');
          if (targetId === '#') return;
          var target = document.querySelector(targetId);
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        });
      }
    }

    /* ===== 7. Counters ===== */
    function initCounters() {
      var counters = document.querySelectorAll('.counter');
      if (!counters.length) return;

      var animated = false;
      var observer = null;

      function animateCounter(el) {
        var target = parseInt(el.getAttribute('data-target'), 10);
        if (isNaN(target)) return;
        var duration = 2000;
        var startTime = performance.now();

        function update(currentTime) {
          var progress = Math.min((currentTime - startTime) / duration, 1);
          var value = Math.floor(progress * target);
          el.textContent = value.toLocaleString();
          if (progress < 1) {
            requestAnimationFrame(update);
          } else {
            el.textContent = target.toLocaleString();
          }
        }
        requestAnimationFrame(update);
      }

      function handleIntersect(entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting && !animated) {
            animated = true;
            for (var j = 0; j < counters.length; j++) {
              animateCounter(counters[j]);
            }
            if (observer) observer.disconnect();
            break;
          }
        }
      }

      if ('IntersectionObserver' in window) {
        observer = new IntersectionObserver(handleIntersect, { threshold: 0.3 });
        for (var k = 0; k < counters.length; k++) {
          observer.observe(counters[k]);
        }
      } else {
        // Fallback: animate immediately
        for (var m = 0; m < counters.length; m++) {
          animateCounter(counters[m]);
        }
      }
    }

    /* ===== 8. Reveal Animations (AOS-like) ===== */
    function initRevealAnimations() {
      var elements = document.querySelectorAll('[data-aos]');
      if (!elements.length) return;

      var observer = null;
      if ('IntersectionObserver' in window) {
        observer = new IntersectionObserver(function(entries) {
          for (var i = 0; i < entries.length; i++) {
            if (entries[i].isIntersecting) {
              var el = entries[i].target;
              var delay = parseInt(el.getAttribute('data-aos-delay'), 10) || 0;
              setTimeout(function() {
                el.classList.add('aos-animate');
              }, delay);
              observer.unobserve(el);
            }
          }
        }, { threshold: 0.15 });

        for (var j = 0; j < elements.length; j++) {
          observer.observe(elements[j]);
        }
      } else {
        // Fallback: show all
        for (var k = 0; k < elements.length; k++) {
          elements[k].classList.add('aos-animate');
        }
      }
    }

    /* ===== 9. Newsletter Validation ===== */
    function initNewsletterValidation() {
      var form = document.getElementById('newsletter-form');
      if (!form) return;

      form.addEventListener('submit', function(e) {
        e.preventDefault();
        var input = this.querySelector('input[type="email"]');
        if (!input) return;

        var email = input.value.trim();
        var isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

        // Simple feedback
        var feedback = this.querySelector('.newsletter-feedback');
        if (!feedback) {
          feedback = document.createElement('span');
          feedback.className = 'newsletter-feedback';
          this.appendChild(feedback);
        }

        if (isValid) {
          feedback.textContent = '✅ Thanks for subscribing!';
          feedback.style.color = 'green';
          input.value = '';
        } else {
          feedback.textContent = '⚠️ Please enter a valid email address.';
          feedback.style.color = '#d9534f';
        }

        setTimeout(function() {
          feedback.textContent = '';
        }, 4000);
      });
    }

    /* ===== 10. Navigation (active link highlight) ===== */
    function initNavigation() {
      var navLinks = document.querySelectorAll('.navbar-nav .nav-link');
      if (!navLinks.length) return;

      var currentPath = window.location.pathname;

      for (var i = 0; i < navLinks.length; i++) {
        var href = navLinks[i].getAttribute('href');
        if (href && href !== '#' && currentPath.indexOf(href) !== -1) {
          navLinks[i].classList.add('active');
        }
      }
    }

    /* ===== 11. Reviews Carousel ===== */
    function initReviewsCarousel() {
      var slides = document.querySelectorAll('.review-slide');
      var dots = document.querySelectorAll('.dot');
      var prevBtn = document.querySelector('.carousel-prev');
      var nextBtn = document.querySelector('.carousel-next');
      if (!slides.length || !dots.length) return;

      var current = 0;
      var total = slides.length;
      var interval = null;

      function goTo(index) {
        for (var i = 0; i < slides.length; i++) {
          slides[i].classList.toggle('active', i === index);
        }
        for (var j = 0; j < dots.length; j++) {
          dots[j].classList.toggle('active', j === index);
        }
        current = index;
      }

      function next() {
        goTo((current + 1) % total);
      }

      function prev() {
        goTo((current - 1 + total) % total);
      }

      if (prevBtn) prevBtn.addEventListener('click', prev);
      if (nextBtn) nextBtn.addEventListener('click', next);

      for (var k = 0; k < dots.length; k++) {
        (function(index) {
          dots[k].addEventListener('click', function() {
            goTo(index);
          });
        })(k);
      }

      // Auto-play reviews
      interval = setInterval(next, 6000);

      // Pause on hover
      var container = document.querySelector('.reviews-carousel');
      if (container) {
        container.addEventListener('mouseenter', function() {
          clearInterval(interval);
        });
        container.addEventListener('mouseleave', function() {
          interval = setInterval(next, 6000);
        });
      }

      // Keyboard support
      document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') prev();
        if (e.key === 'ArrowRight') next();
      });
    }

    /* ===== 12. Initialize Everything ===== */
    function init() {
      // Sliders (only if lightSlider is available)
      if (typeof $ !== 'undefined' && typeof $.fn.lightSlider === 'function') {
        initDestinationsSlider();
        initPackagesSlider();
      } else {
        // Fallback: show static content
        console.warn('lightSlider not available, sliders will not be interactive.');
      }

      // Theme Toggle - IMPROVED
      initThemeToggle();

      // Other features
      initCookiePopup();
      initBackToTop();
      initSmoothScroll();
      initCounters();
      initRevealAnimations();
      initNewsletterValidation();
      initNavigation();
      initReviewsCarousel();

      console.log('✨ Shidow TOURS – All systems ready.');
    }

    // Start
    init();

  }); // end DOMContentLoaded

})();
