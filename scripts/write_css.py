"""One-shot script: overwrite alaska.css with the full redesigned stylesheet."""
import os

CSS = r"""/* ==========================================================================
   Haven Health — Design System
   Brand: Haven Health Vault
   Tagline: "Where every story finds its strength."
   
   Typography: Inter (UI) + Merriweather (editorial headings)
   Palette:  Warm whites, sage greens, soft slate blues — clinical
             warmth without sterility.
   
   Author's note: This file is hand-structured into logical sections.
   No utility-class spam — every rule has a reason.
   ========================================================================== */

/* ── Fonts ────────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@400;700&display=swap');

/* ── Design Tokens ────────────────────────────────────────────────────────── */
:root {
  /* Palette — inspired by Pacific Northwest clinical interiors */
  --white:       #ffffff;
  --snow:        #fafbfc;
  --cloud:       #f3f5f7;
  --mist:        #e8ecf1;
  --slate-100:   #d1d7e0;
  --slate-200:   #b0b9c6;
  --slate-400:   #6b7a8d;
  --slate-600:   #455368;
  --slate-800:   #1e2a3a;
  --sage-50:     #f0f5f1;
  --sage-100:    #dce8de;
  --sage-300:    #8db897;
  --sage:        #4a8c5c;
  --sage-dark:   #3a7049;
  --teal:        #2a7d8a;
  --teal-light:  #e6f4f6;
  --sky:         #3b82c4;
  --coral:       #d9534f;
  --coral-light: #fdf2f2;
  --amber:       #d4930a;
  --amber-light: #fefcf3;

  /* Semantic aliases */
  --c-bg:        var(--snow);
  --c-surface:   var(--white);
  --c-surface-alt:var(--cloud);
  --c-border:    var(--mist);
  --c-border-strong: var(--slate-100);
  --c-text:      var(--slate-800);
  --c-text-secondary: var(--slate-400);
  --c-heading:   var(--slate-800);
  --c-primary:   var(--sage);
  --c-primary-hover: var(--sage-dark);
  --c-primary-soft: var(--sage-50);
  --c-accent:    var(--teal);
  --c-accent-soft: var(--teal-light);
  --c-danger:    var(--coral);
  --c-danger-soft: var(--coral-light);
  --c-warning:   var(--amber);
  --c-warning-soft: var(--amber-light);
  --c-link:      var(--sky);

  /* Typography */
  --font-ui:     'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-editorial: 'Merriweather', 'Georgia', serif;

  /* Spacing scale (4px base) */
  --sp-1: 4px;   --sp-2: 8px;   --sp-3: 12px;  --sp-4: 16px;
  --sp-5: 20px;  --sp-6: 24px;  --sp-8: 32px;  --sp-10: 40px;
  --sp-12: 48px; --sp-16: 64px; --sp-20: 80px; --sp-24: 96px;

  /* Shape */
  --radius-sm:   6px;
  --radius:      10px;
  --radius-lg:   16px;
  --radius-full: 999px;

  /* Elevation */
  --shadow-xs:   0 1px 2px rgba(30,42,58,.05);
  --shadow-sm:   0 1px 3px rgba(30,42,58,.08), 0 1px 2px rgba(30,42,58,.06);
  --shadow:      0 4px 12px rgba(30,42,58,.08);
  --shadow-md:   0 8px 24px rgba(30,42,58,.10);
  --shadow-lg:   0 16px 40px rgba(30,42,58,.12);

  /* Motion */
  --ease:        cubic-bezier(.25,.1,.25,1);
  --duration:    180ms;
  --duration-md: 280ms;

  /* Layout */
  --max-w:       1200px;
  --max-w-narrow:720px;
  --nav-h:       72px;
}


/* ── Reset & Base ─────────────────────────────────────────────────────────── */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-ui);
  color: var(--c-text);
  background: var(--c-bg);
  line-height: 1.65;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

img { max-width: 100%; height: auto; display: block; }
ul, ol { list-style: none; }
a {
  color: var(--c-link);
  text-decoration: none;
  transition: color var(--duration) var(--ease);
}
a:hover { color: var(--c-primary); }

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-editorial);
  color: var(--c-heading);
  line-height: 1.3;
  font-weight: 700;
}

/* Skip-to-content (a11y) */
.skip-link {
  position: absolute;
  left: -9999px;
  top: var(--sp-2);
  background: var(--c-primary);
  color: var(--white);
  padding: var(--sp-2) var(--sp-4);
  border-radius: var(--radius-sm);
  z-index: 200;
  font-weight: 600;
}
.skip-link:focus {
  left: var(--sp-4);
}


/* ── Utility classes ──────────────────────────────────────────────────────── */
.container    { width: 100%; max-width: var(--max-w); margin: 0 auto; padding: 0 var(--sp-6); }
.muted        { color: var(--c-text-secondary); font-size: 0.875rem; }
.text-center  { text-align: center; }
.sr-only      { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }


/* ── Flash / Toast ────────────────────────────────────────────────────────── */
.flash {
  background: var(--c-primary-soft);
  color: var(--c-primary);
  border-bottom: 1px solid var(--sage-100);
  text-align: center;
  padding: var(--sp-3) var(--sp-4);
  font-weight: 500;
  font-size: 0.9rem;
}


/* ==========================================================================
   NAVIGATION
   ========================================================================== */
.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--c-border);
  height: var(--nav-h);
}

.header-inner {
  display: flex;
  align-items: center;
  height: var(--nav-h);
  gap: var(--sp-4);
}

/* ── Brand ── */
.brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  text-decoration: none;
  flex-shrink: 0;
}
.brand-logo {
  height: 36px;
  width: auto;
}
.brand-mark {
  font-family: var(--font-editorial);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--c-heading);
  letter-spacing: -.01em;
}
.brand-sub {
  font-family: var(--font-ui);
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--c-text-secondary);
  display: none;
}
@media (min-width: 900px) {
  .brand-sub { display: inline; }
}

/* ── Nav links ── */
.site-nav,
.site-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}
.site-nav { margin-left: auto; }
.site-actions { margin-left: var(--sp-2); }

.site-nav a,
.site-actions a {
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--c-text-secondary);
  transition: all var(--duration) var(--ease);
  white-space: nowrap;
}
.site-nav a:hover,
.site-actions a:hover {
  color: var(--c-text);
  background: var(--c-surface-alt);
}

.action-primary {
  background: var(--c-primary) !important;
  color: var(--white) !important;
  font-weight: 600 !important;
}
.action-primary:hover {
  background: var(--c-primary-hover) !important;
}

/* Hamburger toggle (mobile) */
.nav-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--sp-2);
  margin-left: auto;
}
.nav-toggle span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--c-text);
  margin: 5px 0;
  border-radius: 2px;
  transition: all var(--duration) var(--ease);
}


/* ==========================================================================
   HERO
   ========================================================================== */
.hero {
  position: relative;
  min-height: 520px;
  display: flex;
  align-items: center;
  background-size: cover;
  background-position: center 40%;
  overflow: hidden;
}
.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(30,42,58,.62) 0%, rgba(74,140,92,.35) 100%);
}
.hero-content {
  position: relative;
  z-index: 2;
  max-width: 640px;
  padding: var(--sp-16) var(--sp-6);
}
.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  background: rgba(255,255,255,.18);
  backdrop-filter: blur(6px);
  padding: var(--sp-2) var(--sp-4);
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--white);
  margin-bottom: var(--sp-5);
  letter-spacing: .03em;
  text-transform: uppercase;
}
.hero-title {
  font-family: var(--font-editorial);
  font-size: clamp(2rem, 5vw, 3rem);
  color: var(--white);
  margin-bottom: var(--sp-4);
  line-height: 1.2;
  letter-spacing: -.02em;
}
.hero-lead {
  font-size: 1.1rem;
  color: rgba(255,255,255,.85);
  line-height: 1.7;
  margin-bottom: var(--sp-8);
  max-width: 520px;
}
.hero-actions {
  display: flex;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

/* Trust bar beneath hero */
.trust-bar {
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  padding: var(--sp-5) 0;
}
.trust-bar-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-10);
  flex-wrap: wrap;
}
.trust-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  color: var(--c-text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}
.trust-icon {
  width: 20px;
  height: 20px;
  color: var(--c-primary);
  flex-shrink: 0;
}


/* ==========================================================================
   SECTIONS — Homepage modules
   ========================================================================== */

/* ── Section wrapper ── */
.section {
  padding: var(--sp-20) 0;
}
.section-alt {
  background: var(--c-surface-alt);
}
.section-header {
  text-align: center;
  max-width: 600px;
  margin: 0 auto var(--sp-12);
}
.section-label {
  display: inline-block;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--c-primary);
  margin-bottom: var(--sp-3);
}
.section-title {
  font-size: clamp(1.5rem, 3vw, 2.125rem);
  margin-bottom: var(--sp-4);
}
.section-subtitle {
  color: var(--c-text-secondary);
  font-size: 1.05rem;
  line-height: 1.7;
}

/* ── Services grid ── */
.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--sp-6);
}
.service-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: var(--sp-8);
  transition: box-shadow var(--duration-md) var(--ease), transform var(--duration-md) var(--ease);
}
.service-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}
.service-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius);
  background: var(--c-primary-soft);
  color: var(--c-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--sp-5);
}
.service-icon svg { width: 24px; height: 24px; }
.service-card h3 {
  font-family: var(--font-ui);
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: var(--sp-2);
}
.service-card p {
  color: var(--c-text-secondary);
  font-size: 0.9rem;
  line-height: 1.65;
}

/* ── About split ── */
.about-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-16);
  align-items: center;
}
.about-image {
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}
.about-image img {
  width: 100%;
  object-fit: cover;
  aspect-ratio: 4/3;
}
.about-body h2 {
  font-size: 1.75rem;
  margin-bottom: var(--sp-4);
}
.about-body p {
  color: var(--c-text-secondary);
  margin-bottom: var(--sp-4);
  line-height: 1.75;
}
.about-body p:last-of-type { margin-bottom: var(--sp-6); }

/* ── Testimonials ── */
.testimonials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--sp-6);
}
.testimonial-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: var(--sp-8);
}
.testimonial-quote {
  font-family: var(--font-editorial);
  font-size: 1rem;
  font-style: italic;
  color: var(--c-text);
  line-height: 1.75;
  margin-bottom: var(--sp-6);
  position: relative;
  padding-left: var(--sp-6);
}
.testimonial-quote::before {
  content: '\201C';
  position: absolute;
  left: 0;
  top: -4px;
  font-size: 2.5rem;
  color: var(--c-primary);
  line-height: 1;
  font-family: var(--font-editorial);
}
.testimonial-author {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.testimonial-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--sage-100);
  color: var(--c-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
}
.testimonial-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--c-text);
}
.testimonial-role {
  font-size: 0.8rem;
  color: var(--c-text-secondary);
}

/* ── Programs / Solutions ── */
.programs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--sp-6);
}
.program-card {
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  transition: box-shadow var(--duration-md) var(--ease);
}
.program-card:hover {
  box-shadow: var(--shadow-md);
}
.program-visual {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
}
.program-visual-green  { background: var(--sage-50); }
.program-visual-blue   { background: var(--teal-light); }
.program-visual-warm   { background: var(--amber-light); }
.program-body {
  padding: var(--sp-5) var(--sp-6) var(--sp-6);
}
.program-body h3 {
  font-family: var(--font-ui);
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--sp-2);
}
.program-body p {
  color: var(--c-text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
}

/* ── How-it-works steps ── */
.steps-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--sp-8);
  counter-reset: step;
}
.step-item {
  text-align: center;
  counter-increment: step;
}
.step-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--c-primary);
  color: var(--white);
  font-weight: 700;
  font-size: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--sp-4);
}
.step-item h3 {
  font-family: var(--font-ui);
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--sp-2);
}
.step-item p {
  color: var(--c-text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
}

/* ── CTA Banner ── */
.cta-banner {
  background: var(--c-primary);
  color: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--sp-16) var(--sp-8);
  text-align: center;
  margin: var(--sp-8) 0;
}
.cta-banner h2 {
  color: var(--white);
  font-size: 1.75rem;
  margin-bottom: var(--sp-3);
}
.cta-banner p {
  color: rgba(255,255,255,.85);
  font-size: 1.05rem;
  margin-bottom: var(--sp-8);
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}

/* ── Blog preview ── */
.blog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--sp-6);
}
.blog-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: box-shadow var(--duration-md) var(--ease);
}
.blog-card:hover { box-shadow: var(--shadow-md); }
.blog-thumb {
  height: 180px;
  background: var(--c-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
}
.blog-body {
  padding: var(--sp-5) var(--sp-6) var(--sp-6);
}
.blog-meta {
  font-size: 0.78rem;
  color: var(--c-text-secondary);
  margin-bottom: var(--sp-2);
}
.blog-body h3 {
  font-family: var(--font-ui);
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--sp-2);
  color: var(--c-heading);
}
.blog-body p {
  color: var(--c-text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
}
.blog-link {
  display: inline-block;
  margin-top: var(--sp-3);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--c-primary);
}
.blog-link:hover { color: var(--c-primary-hover); }


/* ==========================================================================
   MAIN CONTENT AREA (inner pages)
   ========================================================================== */
.main {
  flex: 1;
  padding: var(--sp-10) var(--sp-6);
  max-width: var(--max-w);
  width: 100%;
  margin: 0 auto;
}

/* When the homepage has a hero, the main block should have no top padding */
.home .main { padding-top: 0; }


/* ==========================================================================
   CARDS
   ========================================================================== */
.card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: var(--sp-8);
  box-shadow: var(--shadow-sm);
  max-width: 520px;
  margin: 0 auto;
}
.card h2 {
  font-family: var(--font-editorial);
  font-size: 1.4rem;
  margin-bottom: var(--sp-6);
  padding-bottom: var(--sp-4);
  border-bottom: 1px solid var(--c-border);
}
.card-wide { max-width: 960px; }


/* ==========================================================================
   FORMS
   ========================================================================== */
label {
  display: block;
  font-weight: 500;
  font-size: 0.8rem;
  color: var(--c-text-secondary);
  margin-bottom: var(--sp-1);
  margin-top: var(--sp-4);
  text-transform: uppercase;
  letter-spacing: .04em;
}

input[type=email],
input[type=password],
input[type=text],
textarea,
select {
  width: 100%;
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-surface);
  border: 1px solid var(--c-border-strong);
  border-radius: var(--radius-sm);
  color: var(--c-text);
  font-family: var(--font-ui);
  font-size: 0.925rem;
  transition: border-color var(--duration) var(--ease), box-shadow var(--duration) var(--ease);
  outline: none;
}
input:focus,
textarea:focus,
select:focus {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px rgba(74,140,92,.12);
}

input[type=file] {
  width: 100%;
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-surface-alt);
  border: 2px dashed var(--c-border-strong);
  border-radius: var(--radius-sm);
  color: var(--c-text);
  font-family: var(--font-ui);
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color var(--duration) var(--ease);
}
input[type=file]:hover {
  border-color: var(--c-primary);
}

textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.6;
}
select { cursor: pointer; }


/* ==========================================================================
   BUTTONS
   ========================================================================== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: 10px 24px;
  font-family: var(--font-ui);
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  text-decoration: none;
  color: var(--white);
  background: var(--c-primary);
  line-height: 1.4;
}
.btn:hover {
  background: var(--c-primary-hover);
  box-shadow: var(--shadow-sm);
  color: var(--white);
}

/* Ghost / secondary */
.btn.secondary,
.btn-secondary {
  background: var(--c-surface);
  color: var(--c-text);
  border: 1px solid var(--c-border-strong);
}
.btn.secondary:hover,
.btn-secondary:hover {
  background: var(--c-surface-alt);
  color: var(--c-text);
  box-shadow: none;
}

/* White ghost (for dark backgrounds) */
.btn-white {
  background: var(--white);
  color: var(--c-primary);
  font-weight: 600;
}
.btn-white:hover {
  background: var(--cloud);
  color: var(--c-primary-hover);
}

.btn-outline-white {
  background: transparent;
  color: var(--white);
  border: 2px solid rgba(255,255,255,.5);
}
.btn-outline-white:hover {
  border-color: var(--white);
  background: rgba(255,255,255,.1);
  color: var(--white);
}

/* Danger */
.btn-danger {
  background: var(--c-danger);
}
.btn-danger:hover {
  background: #c9302c;
  box-shadow: 0 2px 8px rgba(217,83,79,.2);
}

/* Sizes */
.btn-sm { padding: 6px 16px; font-size: 0.8rem; }
.btn-lg { padding: 14px 32px; font-size: 1rem; }

/* Group */
.btn-group {
  display: flex;
  gap: var(--sp-3);
  margin-top: var(--sp-5);
  flex-wrap: wrap;
}


/* ── OAuth divider ── */
.oauth-divider {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin: var(--sp-6) 0;
  color: var(--c-text-secondary);
  font-size: 0.82rem;
}
.oauth-divider::before,
.oauth-divider::after {
  content: '';
  flex: 1;
  border-top: 1px solid var(--c-border);
}


/* ==========================================================================
   ENTRY GRID & CARDS (patient / admin / profile)
   ========================================================================== */
.entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--sp-5);
  margin-top: var(--sp-5);
}
.entry-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: var(--sp-5) var(--sp-6);
  transition: box-shadow var(--duration-md) var(--ease), transform var(--duration-md) var(--ease);
  border-left: 4px solid var(--c-primary);
}
.entry-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}
.entry-card__title {
  font-family: var(--font-ui);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--c-heading);
  margin-bottom: var(--sp-1);
  word-break: break-word;
}
.entry-card__meta {
  font-size: 0.78rem;
  color: var(--c-text-secondary);
  margin-bottom: var(--sp-3);
}
.entry-card__narrative {
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-surface-alt);
  border-radius: var(--radius-sm);
  font-style: italic;
  color: var(--c-text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--sp-4);
  line-height: 1.6;
}
.entry-card__actions {
  display: flex;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

/* ── Stat cards (profile) ── */
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--sp-4);
  margin-bottom: var(--sp-8);
}
.stat-card {
  background: var(--c-surface-alt);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: var(--sp-5);
  text-align: center;
}
.stat-card__value {
  font-family: var(--font-editorial);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--c-primary);
}
.stat-card__label {
  font-size: 0.78rem;
  color: var(--c-text-secondary);
  margin-top: var(--sp-1);
  text-transform: uppercase;
  letter-spacing: .04em;
}

/* ── Empty state ── */
.empty-state {
  text-align: center;
  padding: var(--sp-16) var(--sp-6);
  background: var(--c-surface-alt);
  border: 2px dashed var(--c-border);
  border-radius: var(--radius-lg);
}
.empty-state p {
  color: var(--c-text-secondary);
  font-size: 1.05rem;
  margin-bottom: var(--sp-5);
}

/* ── Badge ── */
.badge {
  display: inline-block;
  padding: 2px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: .04em;
}
.badge-primary { background: var(--c-primary-soft); color: var(--c-primary); }
.badge-accent  { background: var(--c-accent-soft); color: var(--c-accent); }


/* ==========================================================================
   ASK ME / AI
   ========================================================================== */
.ai-response {
  padding: var(--sp-6);
  background: var(--c-primary-soft);
  border-left: 4px solid var(--c-primary);
  border-radius: var(--radius);
  margin-top: var(--sp-8);
}
.ai-response h3 {
  font-family: var(--font-ui);
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--sp-3);
}
.ai-response__body {
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--c-text);
  font-size: 0.925rem;
}
.ai-result-item {
  padding: var(--sp-4);
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  margin-top: var(--sp-3);
}
.example-box {
  margin-top: var(--sp-8);
  padding: var(--sp-5) var(--sp-6);
  background: var(--c-surface-alt);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
}
.example-box h4 {
  font-family: var(--font-ui);
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: var(--sp-3);
  color: var(--c-heading);
}
.example-box li {
  color: var(--c-text-secondary);
  padding: var(--sp-1) 0;
  font-size: 0.875rem;
  padding-left: var(--sp-5);
  position: relative;
}
.example-box li::before {
  content: '\2192';
  position: absolute;
  left: 0;
  color: var(--c-primary);
}


/* ==========================================================================
   HISTORY / DIFF
   ========================================================================== */
.commit-list { margin-top: var(--sp-5); }
.commit-item {
  padding: var(--sp-5);
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  margin-bottom: var(--sp-3);
}
.commit-item__sha {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: var(--c-accent);
  background: var(--c-accent-soft);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}
.diff-block {
  white-space: pre-wrap;
  overflow-x: auto;
  padding: var(--sp-5);
  background: var(--slate-800);
  color: var(--mist);
  border-radius: var(--radius);
  font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  margin-top: var(--sp-5);
}


/* ==========================================================================
   INFO PAGES
   ========================================================================== */
.info-section {
  max-width: var(--max-w-narrow);
  margin: 0 auto;
}
.info-section h1 {
  font-size: 2rem;
  margin-bottom: var(--sp-4);
}
.info-section p {
  color: var(--c-text-secondary);
  line-height: 1.8;
  font-size: 1rem;
  margin-bottom: var(--sp-4);
}
.info-section p:last-child { margin-bottom: 0; }


/* ==========================================================================
   FOOTER
   ========================================================================== */
.site-footer {
  background: var(--slate-800);
  color: var(--slate-200);
  margin-top: auto;
  padding: var(--sp-16) 0 var(--sp-10);
}
.footer-inner {
  display: grid;
  grid-template-columns: 2fr repeat(3, 1fr);
  gap: var(--sp-10);
}
.footer-brand-text {
  font-family: var(--font-editorial);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--white);
  margin-bottom: var(--sp-3);
}
.footer-tagline {
  font-size: 0.85rem;
  color: var(--slate-200);
  line-height: 1.6;
  margin-bottom: var(--sp-5);
  max-width: 280px;
}
.footer-title {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 0.82rem;
  color: var(--white);
  margin-bottom: var(--sp-4);
  text-transform: uppercase;
  letter-spacing: .06em;
}
.footer-links {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.footer-links a {
  font-size: 0.85rem;
  color: var(--slate-200);
  transition: color var(--duration) var(--ease);
}
.footer-links a:hover {
  color: var(--white);
}
.footer-bottom {
  margin-top: var(--sp-10);
  padding-top: var(--sp-6);
  border-top: 1px solid rgba(255,255,255,.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-4);
}
.footer-copy {
  font-size: 0.78rem;
  color: var(--slate-400);
}
.footer-socials {
  display: flex;
  gap: var(--sp-3);
}
.footer-social-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--slate-200);
  transition: all var(--duration) var(--ease);
  text-decoration: none;
}
.footer-social-icon:hover {
  background: var(--c-primary);
  color: var(--white);
  border-color: var(--c-primary);
}


/* ==========================================================================
   RESPONSIVE
   ========================================================================== */
@media (max-width: 768px) {
  /* Nav collapses */
  .nav-toggle { display: block; }
  .site-nav,
  .site-actions {
    display: none;
    width: 100%;
    flex-direction: column;
    gap: 0;
  }
  .site-nav a,
  .site-actions a {
    padding: var(--sp-3) var(--sp-4);
    border-radius: 0;
    border-bottom: 1px solid var(--c-border);
  }
  .header-inner {
    flex-wrap: wrap;
    height: auto;
    padding: var(--sp-3) var(--sp-6);
  }
  .header-inner.nav-open .site-nav,
  .header-inner.nav-open .site-actions { display: flex; }

  /* Hero */
  .hero { min-height: 400px; }
  .hero-content { padding: var(--sp-12) var(--sp-6); }
  .hero-title { font-size: 1.8rem; }

  /* Sections */
  .section { padding: var(--sp-12) 0; }
  .about-split { grid-template-columns: 1fr; gap: var(--sp-8); }

  /* Cards & grids */
  .main { padding: var(--sp-6) var(--sp-4); }
  .card { padding: var(--sp-6); }
  .entry-grid { grid-template-columns: 1fr; }
  .stat-row { grid-template-columns: 1fr; }

  /* Footer */
  .footer-inner { grid-template-columns: 1fr; gap: var(--sp-8); }
}

@media (max-width: 480px) {
  .hero-actions { flex-direction: column; }
  .hero-actions .btn { width: 100%; }
  .trust-bar-inner { flex-direction: column; gap: var(--sp-4); }
  .card { padding: var(--sp-5) var(--sp-4); }
  .services-grid { grid-template-columns: 1fr; }
}

@media (min-width: 769px) {
  .nav-toggle { display: none !important; }
}


/* ==========================================================================
   ANIMATIONS (subtle, purposeful)
   ========================================================================== */
@media (prefers-reduced-motion: no-preference) {
  .fade-in {
    opacity: 0;
    transform: translateY(16px);
    transition: opacity 0.5s var(--ease), transform 0.5s var(--ease);
  }
  .fade-in.visible {
    opacity: 1;
    transform: translateY(0);
  }
}
"""

target = os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'alaska.css')
target = os.path.abspath(target)
with open(target, 'w', encoding='utf-8') as f:
    f.write(CSS)
print(f"Wrote {len(CSS):,} chars to {target}")
