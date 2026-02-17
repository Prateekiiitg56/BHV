/* ==========================================================================
   Haven Health — app.js
   Minimal, purposeful JavaScript
   ========================================================================== */

(function () {
  'use strict';

  /* ── Mobile nav toggle ── */
  const toggle = document.querySelector('.nav-toggle');
  const headerInner = document.querySelector('.header-inner');

  if (toggle && headerInner) {
    toggle.addEventListener('click', function () {
      headerInner.classList.toggle('nav-open');
      const expanded = headerInner.classList.contains('nav-open');
      toggle.setAttribute('aria-expanded', expanded);
    });

    // Close mobile nav when clicking a link
    headerInner.querySelectorAll('.site-nav a, .site-actions a').forEach(function (link) {
      link.addEventListener('click', function () {
        headerInner.classList.remove('nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ── Intersection Observer: fade-in on scroll ── */
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('.fade-in').forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ── Auto-dismiss flash messages ── */
  var flash = document.querySelector('.flash');
  if (flash) {
    setTimeout(function () {
      flash.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      flash.style.opacity = '0';
      flash.style.transform = 'translateY(-100%)';
      setTimeout(function () { flash.remove(); }, 450);
    }, 4500);
  }

  /* ── Dark / Light mode toggle ── */
  var themeToggle = document.querySelector('.theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var html = document.documentElement;
      var current = html.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('bhv-theme', next);
    });
  }

  // Also listen for OS-level preference changes (if user hasn't manually toggled)
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      // Only auto-switch if user hasn't manually set a preference
      var stored = localStorage.getItem('bhv-theme');
      if (!stored) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      }
    });
  }

})();
