/* =============================================================
   CIRQEN Medical - main.js
   ============================================================= */

"use strict";

const qs = (s, root = document) => root.querySelector(s);
const qsa = (s, root = document) => [...root.querySelectorAll(s)];

function debounce(fn, ms = 80) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

const state = {
  scrollY: 0,
  lastScrollY: 0,
  sections: [],
  activeSection: "",
};

const progressBar = qs("#scroll-progress");

function updateProgress() {
  if (!progressBar) return;
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
  progressBar.style.width = pct + "%";
}

const navbar = qs("#nav");
const navMenu = qs("#navLinks");
const menuToggle = qs("#navToggle");

function updateNavbar() {
  if (!navbar) return;
  if (window.scrollY > 80) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
}

function closeMobileMenu() {
  if (!navMenu || !menuToggle) return;
  navMenu.classList.remove("open");
  menuToggle.classList.remove("open");
  menuToggle.setAttribute("aria-expanded", "false");
  document.body.classList.remove("nav-open");
}

if (menuToggle && navMenu) {
  menuToggle.setAttribute("aria-expanded", "false");

  menuToggle.addEventListener("click", () => {
    const isOpen = navMenu.classList.toggle("open");
    menuToggle.classList.toggle("open", isOpen);
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    document.body.classList.toggle("nav-open", isOpen);
  });

  // Close when a nav link is tapped
  qsa("a", navMenu).forEach((link) => {
    link.addEventListener("click", closeMobileMenu);
  });

  // Close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMobileMenu();
  });

  // Close if window is resized back to desktop width
  window.addEventListener(
    "resize",
    debounce(() => {
      if (window.innerWidth > 768) closeMobileMenu();
    }, 150),
  );
}

document.addEventListener("click", (e) => {
  const link = e.target.closest('a[href^="#"]');
  if (!link) return;
  const href = link.getAttribute("href");
  if (href === "#") return;
  const target = qs(href);
  if (!target) return;
  e.preventDefault();
  const navH = navbar ? navbar.offsetHeight + 8 : 8;
  const top = target.getBoundingClientRect().top + window.scrollY - navH;
  window.scrollTo({ top, behavior: "smooth" });
});

function buildSectionDots() {
  const dotsNav = qs("#section-dots");
  const sections = qsa("section[data-section]");
  state.sections = sections;
  if (!dotsNav) return;

  sections.forEach((sec) => {
    const dot = document.createElement("div");
    dot.className = "section-dot";
    dot.setAttribute("data-label", sec.dataset.section);
    dot.setAttribute("aria-label", sec.dataset.section);
    dot.addEventListener("click", () => {
      const navH = navbar ? navbar.offsetHeight + 8 : 8;
      const top = sec.getBoundingClientRect().top + window.scrollY - navH;
      window.scrollTo({ top, behavior: "smooth" });
    });
    dotsNav.appendChild(dot);
  });
}

function updateActiveDot() {
  const dots = qsa(".section-dot");
  const navLinks = qsa(".nav-link");
  const scrollMid = window.scrollY + window.innerHeight * 0.35;

  state.sections.forEach((sec, i) => {
    const top = sec.offsetTop;
    const bottom = top + sec.offsetHeight;
    const isActive = scrollMid >= top && scrollMid < bottom;

    dots[i]?.classList.toggle("active", isActive);

    const id = sec.id;
    const link = qs(`.nav-link[href="#${id}"]`);
    navLinks.forEach((l) => l.classList.remove("active"));
    if (isActive && link) link.classList.add("active");

    if (isActive) state.activeSection = id;
  });
}

function setupAOS() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("aos-animate");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -60px 0px" },
  );

  qsa("[data-aos]").forEach((el) => observer.observe(el));
}

const TARGETS = [
  ".pillar-card",
  ".platform-feature",
  ".impact-card",
  ".serves-card",
  ".solution-card",
  ".stat-card",
  ".contact-item",
  ".feature-tile",
  ".system-card",
  ".service-card",
  ".process-step",
  ".reason-card",
  ".product-category-card",
  ".industry-card",
  ".resource-card",
  ".project-card",
  ".resource-column",
  ".value-card",
  ".mission-vision-card",
];

qsa(TARGETS.join(",")).forEach((el) => {
  el.style.opacity = "0";
  el.style.transform = "translateY(28px)";
  el.style.transition = `
    opacity   0.65s cubic-bezier(0.16,1,0.3,1),
    transform 0.65s cubic-bezier(0.16,1,0.3,1)
  `;
});

const CONTAINERS = [
  ".pillars-grid",
  ".platform-grid",
  ".impact-grid",
  ".serves-grid",
  ".solution-stack",
  ".stats-display",
  ".contact-details",
  ".feature-grid",
  ".software-system-grid",
  ".service-grid",
  ".process-steps",
  ".reason-grid",
  ".product-category-grid",
  ".industry-grid",
  ".resource-grid",
  ".project-grid",
  ".resource-center",
  ".values-grid",
  ".mission-vision-grid",
];

const staggerObs = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const children = qsa(TARGETS.join(","), entry.target);
      children.forEach((child, i) => {
        setTimeout(() => {
          child.style.opacity = "1";
          child.style.transform = "translateY(0)";
        }, i * 80);
      });
      staggerObs.unobserve(entry.target);
    });
  },
  { threshold: 0.08, rootMargin: "0px 0px -40px 0px" },
);

qsa(CONTAINERS.join(",")).forEach((el) => staggerObs.observe(el));

function animateCounter(el, target) {
  const isFloat = String(target).includes(".");
  const decimals = isFloat ? String(target).split(".")[1].length : 0;
  const duration = 2000;
  const startTime = performance.now();

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = lerp(0, target, eased);
    el.textContent = isFloat
      ? current.toFixed(decimals)
      : Math.round(current).toLocaleString();
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

function setupCounters() {
  const counterObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const target = parseFloat(entry.target.getAttribute("data-target"));
        if (!isNaN(target)) animateCounter(entry.target, target);
        counterObs.unobserve(entry.target);
      });
    },
    { threshold: 0.5 },
  );

  qsa(".stat-value[data-target]").forEach((el) => counterObs.observe(el));
}

function setupAboutCarousel() {
  const carousel = qs("#aboutCarousel");
  const track = qs("#carouselTrack");
  const dotsNav = qs("#carouselDots");
  if (!carousel || !track || !dotsNav) return;

  const slides = qsa(".carousel-slide", track);
  if (slides.length <= 1) return;

  let current = 0;
  let timer = null;
  const DELAY = 4000; // 4 s between auto-advances

  const dots = slides.map((_, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "carousel-dot" + (i === 0 ? " active" : "");
    dot.setAttribute("aria-label", `Go to photo ${i + 1}`);
    dot.addEventListener("click", () => goTo(i, true));
    dotsNav.appendChild(dot);
    return dot;
  });

  function update() {
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((dot, i) => dot.classList.toggle("active", i === current));
  }

  function goTo(index, manual = false) {
    current = (index + slides.length) % slides.length;
    update();
    if (manual) restart();
  }

  function next() {
    goTo(current + 1);
  }

  function prev() {
    goTo(current - 1);
  }

  function restart() {
    clearInterval(timer);
    timer = setInterval(next, DELAY);
  }

  // Pause while the user's pointer is on the carousel
  carousel.addEventListener("mouseenter", () => clearInterval(timer));
  carousel.addEventListener("mouseleave", restart);

  // Touch swipe support — and critically, don't hijack vertical page scroll
  let touchStartX = 0;
  let touchStartY = 0;
  let isSwiping = false;

  carousel.addEventListener(
    "touchstart",
    (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      isSwiping = false;
      clearInterval(timer);
    },
    { passive: true },
  );

  carousel.addEventListener(
    "touchmove",
    (e) => {
      const dx = e.touches[0].clientX - touchStartX;
      const dy = e.touches[0].clientY - touchStartY;
      // Only lock horizontal if the gesture is clearly sideways
      if (!isSwiping && Math.abs(dx) > Math.abs(dy) * 1.5 && Math.abs(dx) > 8) {
        isSwiping = true;
      }
      // If it's a vertical scroll, do not interfere
      if (!isSwiping) return;
      e.preventDefault(); // block scroll only for horizontal swipes
    },
    { passive: false },
  );

  carousel.addEventListener(
    "touchend",
    (e) => {
      if (!isSwiping) {
        restart();
        return;
      }
      const dx = e.changedTouches[0].clientX - touchStartX;
      if (Math.abs(dx) > 40) {
        goTo(dx < 0 ? current + 1 : current - 1, true);
      } else {
        restart();
      }
      isSwiping = false;
    },
    { passive: true },
  );

  // Keyboard support when the carousel is focused
  carousel.setAttribute("tabindex", "0");
  carousel.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") {
      prev();
      restart();
    }
    if (e.key === "ArrowRight") {
      next();
      restart();
    }
  });

  update();
  restart();
}

function setupRevealAnimations() {
  const targets = qsa(
    ".section-head, .about-grid > *, .eng-platforms, .eng-metrics, .filter-row, .gallery-item, .rate-row, .contact-grid > *, .fact--card, .brand-card",
  );
  targets.forEach((el) => el.classList.add("reveal"));

  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, i) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        setTimeout(() => el.classList.add("in-view"), (i % 6) * 70);
        obs.unobserve(el);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
  );

  targets.forEach((el) => obs.observe(el));
}

function setupHeroCarousel() {
  const carousel = qs("#heroCarousel");
  const heroSection = qs(".hero");
  if (!carousel || !heroSection) return;

  const slides = qsa(".hero-bg-slide", carousel);
  const prevBtn = qs("#carouselPrev");
  const nextBtn = qs("#carouselNext");
  if (!slides.length) return;

  let current = 0;
  let timer = null;
  const DELAY = 5500;

  // ---- Adaptive text colour via canvas brightness sampling ----
  // We draw a small portion of each slide's background image onto an
  // off-screen canvas and measure the average luminance of the top-left
  // region (where the headline text sits). Light image → dark text,
  // dark image → light text.
  const canvas = document.createElement("canvas");
  canvas.width = 80;
  canvas.height = 60;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });

  // Cache per-slide brightness (null = not sampled yet)
  const brightnessCache = new Array(slides.length).fill(null);

  function getImageUrl(slide) {
    // Extract URL from inline style: background-image: url("...")
    const raw = slide.style.backgroundImage || "";
    const m = raw.match(/url\(["']?([^"')]+)["']?\)/);
    return m ? m[1] : null;
  }

  function sampleBrightness(imageUrl, callback) {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        ctx.drawImage(img, 0, 0, 80, 60);
        const d = ctx.getImageData(0, 0, 80, 60).data;
        let total = 0;
        for (let i = 0; i < d.length; i += 4) {
          // Perceived luminance (ITU-R BT.709)
          total += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
        }
        callback(total / (d.length / 4)); // 0–255
      } catch {
        callback(null); // CORS or tainted canvas — keep light
      }
    };
    img.onerror = () => callback(null);
    img.src = imageUrl;
  }

  function applyTextTheme(slideIndex, brightness) {
    // brightness null or > 140 → image is light → use dark text
    // brightness ≤ 140 → image is dark → use light text
    const isDark = brightness === null || brightness <= 140;
    heroSection.setAttribute("data-hero-theme", isDark ? "light" : "dark");
  }

  function activateSlide(index) {
    slides[current].classList.remove("is-active");
    current = (index + slides.length) % slides.length;
    slides[current].classList.add("is-active");

    const cached = brightnessCache[current];
    if (cached !== null) {
      applyTextTheme(current, cached);
    } else {
      const url = getImageUrl(slides[current]);
      if (url) {
        sampleBrightness(url, (lum) => {
          brightnessCache[current] = lum ?? -1; // -1 = failed, treat as dark
          applyTextTheme(current, lum);
        });
      }
    }
  }

  function goTo(index, manual = false) {
    activateSlide(index);
    if (manual) restart();
  }

  function next() {
    goTo(current + 1);
  }

  function restart() {
    clearInterval(timer);
    timer = setInterval(next, DELAY);
  }

  // Kick off brightness sample for first slide immediately
  activateSlide(0);

  nextBtn?.addEventListener("click", () => goTo(current + 1, true));
  prevBtn?.addEventListener("click", () => goTo(current - 1, true));

  // Pause auto-advance while user hovers the hero
  heroSection.addEventListener("mouseenter", () => clearInterval(timer));
  heroSection.addEventListener("mouseleave", restart);

  restart();
}

function setupWorkGallery() {
  const filterRow = qs("#filterRow");
  const galleryItems = qsa("#gallery .gallery-item");
  if (!filterRow || !galleryItems.length) return;

  function stopMedia(item) {
    const video = qs("video", item);
    if (video && !video.paused) video.pause();
    const iframe = qs("iframe", item);
    if (iframe && iframe.src) iframe.src = iframe.src; // reset embedded players (YouTube/Vimeo)
  }

  filterRow.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;

    qsa(".filter-btn", filterRow).forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-pressed", "false");
    });
    btn.classList.add("active");
    btn.setAttribute("aria-pressed", "true");

    const filter = btn.dataset.filter;
    galleryItems.forEach((item) => {
      const match = filter === "all" || item.dataset.cat === filter;
      if (!match) stopMedia(item);
      item.classList.toggle("hidden", !match);
    });
  });

  // Only one uploaded video plays at a time in the gallery grid
  qsa("#gallery video").forEach((video) => {
    video.addEventListener("play", () => {
      qsa("#gallery video").forEach((other) => {
        if (other !== video) other.pause();
      });
    });
  });
}

function setupFormDefaults() {
  const params = new URLSearchParams(window.location.search);
  const interest = params.get("interest");
  const source = params.get("source");
  const select = qs("#demo-interest") || qs("#id_interest_area");
  const message = qs("#demo-message") || qs("#id_message");

  if (interest && select) {
    const options = Array.from(select.options).map((option) => option.value);
    if (options.includes(interest)) select.value = interest;
  }

  if (source && message && !message.value.trim()) {
    const label = interest || "the Cirqen platform";
    const action =
      source === "quote"
        ? "quote"
        : source === "trial"
          ? "trial"
          : source === "sales"
            ? "sales conversation"
            : "demo";
    message.value = `I am interested in ${label} and would like to request a ${action}.`;
  }
}

function setupGalleryVideoState() {
  qsa(".video-wrap").forEach((wrap) => {
    const item = wrap.closest(".gallery-item");
    if (!item) return;

    const video = qs("video", wrap);
    if (video) {
      video.addEventListener("play", () => item.classList.add("is-playing"));
      video.addEventListener("pause", () =>
        item.classList.remove("is-playing"),
      );
      video.addEventListener("ended", () =>
        item.classList.remove("is-playing"),
      );
    }

    const iframe = qs("iframe", wrap);
    if (iframe) {
      wrap.addEventListener("click", () => item.classList.add("is-playing"));
    }
  });

  document.addEventListener("click", (e) => {
    qsa(".gallery-item.is-playing").forEach((item) => {
      if (!item.contains(e.target)) item.classList.remove("is-playing");
    });
  });
}

function onScroll() {
  state.lastScrollY = state.scrollY;
  state.scrollY = window.scrollY;
  updateProgress();
  updateNavbar();
  updateActiveDot();
}

document.addEventListener("DOMContentLoaded", () => {
  buildSectionDots();
  setupAOS();
  setupCounters();
  setupAboutCarousel();
  setupHeroCarousel();
  setupWorkGallery();
  setupGalleryVideoState();
  setupFormDefaults();
  setupRevealAnimations();

  const yearEl = qs("#copyright-year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  setTimeout(() => {
    qsa("[data-aos]").forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight) el.classList.add("aos-animate");
    });
  }, 80);

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
});
