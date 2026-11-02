(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- mobile menu ---- */
  const nav = document.querySelector('.nav');
  const toggle = document.querySelector('.nav__toggle');
  if (nav && toggle) {
    const setOpen = (open) => {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };
    toggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
    nav.querySelectorAll('.nav__links a').forEach((a) => a.addEventListener('click', () => setOpen(false)));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) { setOpen(false); toggle.focus(); }
    });
  }

  /* ---- entrances: heading, then text, then media, staggered inside each section ---- */
  const groups = new Map();
  document.querySelectorAll('.reveal').forEach((el) => {
    const host = el.closest('section, footer') || document.body;
    const list = groups.get(host) || [];
    el.style.setProperty('--d', `${Math.min(list.length, 6) * 75}ms`);
    list.push(el);
    groups.set(host, list);
  });
  const photo = document.querySelector('.hero__photo');
  const show = (el) => el.classList.add('is-in');
  if (reduce || !('IntersectionObserver' in window)) {
    document.querySelectorAll('.reveal').forEach(show);
    if (photo) show(photo);
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { show(entry.target); io.unobserve(entry.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el));
    if (photo) requestAnimationFrame(() => show(photo));
    // safety net: never leave content hidden
    window.setTimeout(() => document.querySelectorAll('.reveal:not(.is-in)').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight) show(el);
    }), 2500);
  }

  /* ---- the extruder: predict vs. reverse-design ---- */
  const loop = document.querySelector('.loop');
  if (loop) {
    const buttons = loop.querySelectorAll('.seg__btn');
    buttons.forEach((btn) => btn.addEventListener('click', () => {
      const mode = btn.dataset.set;
      loop.dataset.mode = mode;
      buttons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
    }));
  }

  /* ---- publications filter, deep-linked as ?topic= ---- */
  const chips = document.querySelectorAll('.chip');
  const pubs = document.querySelectorAll('.pub');
  const count = document.getElementById('pubs-count');
  const empty = document.querySelector('.pubs__empty');
  const labels = { all: 'all topics' };
  chips.forEach((c) => { labels[c.dataset.topic] = c.textContent.trim(); });

  const applyTopic = (topic, push) => {
    if (!labels[topic]) topic = 'all';
    let shown = 0;
    pubs.forEach((p) => {
      const match = topic === 'all' || p.dataset.topic === topic;
      p.hidden = !match;
      if (match) shown += 1;
    });
    document.querySelectorAll('.pubs').forEach((list) => {
      const head = list.previousElementSibling;
      const any = [...list.children].some((li) => !li.hidden);
      list.hidden = !any;
      if (head && head.classList.contains('pubs__group')) head.hidden = !any;
    });
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.topic === topic)));
    if (empty) empty.hidden = shown !== 0;
    if (count) {
      count.textContent = topic === 'all'
        ? `Showing all ${shown}`
        : `Showing ${shown} of ${pubs.length} in ${labels[topic]}`;
    }
    if (push) {
      const url = new URL(window.location.href);
      if (topic === 'all') url.searchParams.delete('topic'); else url.searchParams.set('topic', topic);
      history.replaceState(null, '', url);
    }
  };
  chips.forEach((c) => c.addEventListener('click', () => applyTopic(c.dataset.topic, true)));
  document.querySelectorAll('.linkbtn[data-topic]').forEach((b) => b.addEventListener('click', () => applyTopic('all', true)));
  try {
    const initial = new URL(window.location.href).searchParams.get('topic');
    if (initial) applyTopic(initial, false);
  } catch (e) { /* keep default */ }

  /* ---- talks: anything already past moves to "Earlier" by itself ---- */
  const upcoming = document.querySelector('.talks--upcoming');
  const past = document.querySelector('.talks--past');
  if (upcoming && past) {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    [...upcoming.children].forEach((li) => {
      const d = new Date(`${li.dataset.date}T23:59:59`);
      if (!Number.isNaN(d.getTime()) && d < today) past.prepend(li);
    });
    const items = [...past.children].sort((a, b) => b.dataset.date.localeCompare(a.dataset.date));
    items.forEach((li) => past.appendChild(li));
    if (!upcoming.children.length) {
      upcoming.hidden = true;
      const h = document.getElementById('talks-upcoming-title');
      if (h) h.hidden = true;
    }
  }
})();
