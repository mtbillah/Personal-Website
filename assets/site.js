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
    document.dispatchEvent(new CustomEvent('pubs:topic', { detail: topic }));
  };
  chips.forEach((c) => c.addEventListener('click', () => applyTopic(c.dataset.topic, true)));
  document.querySelectorAll('.linkbtn[data-topic]').forEach((b) => b.addEventListener('click', () => applyTopic('all', true)));
  try {
    const initial = new URL(window.location.href).searchParams.get('topic');
    if (initial) applyTopic(initial, false);
  } catch (e) { /* keep default */ }

  /* ---- talks: split into "Coming up" and "Earlier" by today's date ---- */
  const upcoming = document.querySelector('.talks--upcoming');
  const past = document.querySelector('.talks--past');
  if (upcoming && past) {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const all = [...upcoming.children, ...past.children];
    const isPast = (li) => {
      const d = new Date(`${li.dataset.date}T23:59:59`);
      return !Number.isNaN(d.getTime()) && d < today;
    };
    all.filter((li) => !isPast(li)).sort((a, b) => a.dataset.date.localeCompare(b.dataset.date)).forEach((li) => upcoming.appendChild(li));
    all.filter(isPast).sort((a, b) => b.dataset.date.localeCompare(a.dataset.date)).forEach((li) => past.appendChild(li));
    const none = !upcoming.children.length;
    upcoming.hidden = none;
    const h = document.getElementById('talks-upcoming-title');
    if (h) h.hidden = none;
  }
  /* ---- "Show all": long lists open with their newest items, the rest one click away ---- */
  const moreGroups = [
    { sec: '#publications', lists: '.pubs', limits: [2, 3], noun: 'publications' },
    { sec: '#talks', lists: '.talks--upcoming, .talks--past', limits: [3, 2], noun: 'talks' },
    { sec: '#experience', lists: '.roles', limits: [3, 2, 2], label: 'Show full experience' },
    { sec: '#teaching', lists: '.students', limits: [4], noun: 'projects' },
    { sec: '#beyond', lists: '.plain', limits: [3, 3, 3, 3], label: 'Show all awards and activities' },
  ];
  const itemsOf = (list) => [...list.children].filter((el) => el.matches('li, div'));
  moreGroups.forEach((g, gi) => {
    const sec = document.querySelector(g.sec);
    if (!sec) return;
    const lists = [...sec.querySelectorAll(g.lists)];
    const total = lists.reduce((n, l) => n + itemsOf(l).length, 0);
    const clipped = () => lists.flatMap((l, i) => itemsOf(l).slice(g.limits[i] ?? g.limits[g.limits.length - 1]));
    if (!clipped().length) return;
    const wrap = sec.querySelector('.wrap');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'more';
    btn.id = `more-${gi}`;
    btn.setAttribute('aria-controls', sec.id);
    const openLabel = g.label || `Show all ${total} ${g.noun}`;
    let open = false;
    let suspended = false;
    const render = () => {
      lists.flatMap(itemsOf).forEach((el) => el.classList.remove('is-clipped'));
      if (!open && !suspended) clipped().forEach((el) => el.classList.add('is-clipped'));
      btn.hidden = suspended;
      btn.setAttribute('aria-expanded', String(open));
      btn.innerHTML = `<span>${open ? 'Show fewer' : openLabel}</span><svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
      if (g.sec === '#publications' && count && !suspended) {
        const visible = [...pubs].filter((p) => !p.classList.contains('is-clipped')).length;
        count.textContent = open ? `Showing all ${pubs.length}` : `Showing ${visible} of ${pubs.length}`;
      }
    };
    btn.addEventListener('click', () => {
      open = !open;
      render();
      if (!open) btn.scrollIntoView({ block: 'nearest', behavior: reduce ? 'auto' : 'smooth' });
    });
    if (g.sec === '#publications') {
      const current = document.querySelector('.chip[aria-pressed="true"]');
      suspended = !!current && current.dataset.topic !== 'all';
      document.addEventListener('pubs:topic', (e) => { suspended = e.detail !== 'all'; render(); });
      (sec.querySelector('.pubs__body') || wrap).appendChild(btn);
    } else {
      wrap.appendChild(btn);
    }
    render();
  });
})();
