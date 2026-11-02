#!/usr/bin/env python3
"""Update index.html from the Overleaf CV (.tex).

Usage:  python3 tools/cv_to_site.py <cv-folder-or-.tex> <index.html> [--check]

Regenerates the regions of index.html wrapped in
    <!-- AUTO:name --> ... <!-- /AUTO:name -->
from the CV: publications, talks, awards / service / badminton, students supervised.
Everything else on the page is hand-written and left alone.

Safety: the script refuses to write (exit code 1) if any section parses to nothing,
or if the number of publications or presentations goes down compared with the page
as it is now. Pass --allow-fewer to accept a deliberate removal.
"""
import datetime as dt
import html
import pathlib
import re
import sys

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}
MON3 = {i: m[:3] for m, i in MONTHS.items()}


# ---------------------------------------------------------------- LaTeX helpers
def strip_comments(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def balanced(s, i):
    """s[i] == '{' -> (content, index after the matching '}')."""
    assert s[i] == "{", s[i:i + 30]
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces near: " + s[i:i + 60])


def args(s, i, n):
    out = []
    for _ in range(n):
        while s[i].isspace():
            i += 1
        a, i = balanced(s, i)
        out.append(a)
    return out, i


def find_cmd(s, name, nargs):
    """All occurrences of \\name{..}{..} (nargs groups)."""
    res = []
    for m in re.finditer(r"\\" + name + r"(?![A-Za-z])", s):
        try:
            a, _ = args(s, m.end(), nargs)
            res.append(a)
        except (ValueError, IndexError, AssertionError):
            pass
    return res


def env_blocks(s, env, with_arg=True):
    """Bodies of \\begin{env}{arg} ... \\end{env} -> list of (arg, body)."""
    out = []
    for m in re.finditer(r"\\begin\{" + env + r"\}", s):
        i = m.end()
        arg = None
        if with_arg:
            (arg,), i = args(s, i, 1)
        end = s.index(r"\end{" + env + "}", i)
        out.append((arg, s[i:end]))
    return out


ME = "\u0001ME\u0001"


def to_html(t, bold=True):
    """Small LaTeX -> HTML converter for CV text."""
    t = t.replace(r"\me", ME)
    t = t.replace(r"\upcoming", "")
    t = t.replace(r"\&", "\u0002AMP\u0002").replace(r"\%", "%")
    t = html.escape(t, quote=False)
    t = t.replace("\u0002AMP\u0002", "&amp;")
    t = re.sub(r"\\'e", "é", t)
    t = re.sub(r"\\'\{e\}", "é", t)
    t = t.replace(r"\textdegree", "°").replace(r"\textperiodcentered", "·")
    for _ in range(4):  # nested
        t = re.sub(r"\\emph\{([^{}]*)\}", r"<em>\1</em>", t)
        t = re.sub(r"\\textit\{([^{}]*)\}", r"<em>\1</em>", t)
        t = re.sub(r"\\textbf\{([^{}]*)\}", (r"<b>\1</b>" if bold else r"\1"), t)
        t = re.sub(r"\\textsc\{([^{}]*)\}", r"\1", t)
        t = re.sub(r"\\(?:small|footnotesize|scriptsize)\b\s*", "", t)
        t = re.sub(r"\\href\{([^{}]*)\}\{([^{}]*)\}", r"\2", t)
    t = t.replace("---", "—").replace("--", "–")
    t = t.replace(r"\,", "\u2009").replace(r"\ ", " ").replace("~", "\u00a0")
    t = t.replace(r"\\", " ")
    t = re.sub(r"\\[A-Za-z]+\*?", "", t)  # any other command
    t = t.replace("{", "").replace("}", "")
    t = t.replace("'", "’").replace("``", "“").replace("''", "”")
    t = re.sub(r"\s+", " ", t).strip()
    me_html = "<b>Billah, M. T.</b>" if bold else "Billah, M. T."
    t = re.sub(ME + r"\*", "<b>Billah, M. T.*</b>" if bold else "Billah, M. T.*", t)
    t = t.replace(ME, me_html)
    return t


def plain(t):
    return re.sub(r"<[^>]+>", "", to_html(t, bold=False))


def section(tex, label_regex):
    """Body of the cvsec whose label matches."""
    for arg, body in env_blocks(tex, "cvsec"):
        if re.search(label_regex, arg.replace("\\\\", " "), re.I):
            return body
    return ""


def cvitems(body):
    return [a[0] for a in find_cmd(body, "cvitem", 1)]


def subsections(body):
    """Split a section at \\cvsub{...} headings -> list of (heading, text)."""
    parts = re.split(r"\\cvsub\{", body)
    out = []
    for p in parts[1:]:
        head, i = balanced("{" + p, 0)
        out.append((plain(head), p[i - 1:]))
    return out


# ---------------------------------------------------------------- parsers
def topic_of(title, venue):
    s = (title + " " + venue).lower()
    if re.search(r"extru|machine learning|artificial intelligence|\bml\b|meat analogue|plant-based", s):
        return "extrusion"
    if re.search(r"dry|dryer|drying", s):
        return "drying"
    if re.search(r"film|packag", s):
        return "packaging"
    return "quality"


def parse_publications(tex):
    pubs = {"published": [], "review": []}
    for key, rx in (("published", r"^Publications"), ("review", r"Submitted")):
        for raw in cvitems(section(tex, rx)):
            h = to_html(raw)
            m = re.search(r"\((\d{4})\)\.\s*", h)
            if m:
                authors, rest, year = h[:m.start()].strip(), h[m.end():], m.group(1)
                tm = re.match(r"(.*?)\.\s*(<em>.*)$", rest)
                title, venue = (tm.group(1), tm.group(2)) if tm else (rest, "")
            else:
                pre, _, post = h.partition("<em>")
                post = "<em>" + post if post else ""
                cut = pre.rstrip().rstrip(".").rfind(". ")
                authors, title = pre[:cut + 1].strip(), pre[cut + 2:].strip().rstrip(".")
                venue, year = post, ("Revision" if "revision" in post.lower() else "In review")
            title = title.strip().rstrip(".")
            if title:
                title = title[0].upper() + title[1:]
            pubs[key].append(dict(year=year, title=title, meta=f"{authors} {venue}".strip(),
                                  topic=topic_of(plain(title), plain(venue))))
    return pubs


DATE_RX = re.compile(r",\s*(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:\s*–\s*(\d{1,2}))?,\s*")


def parse_talk(raw, kind):
    h = to_html(raw)
    m = re.search(r"\((\d{4})\)\.\s*", h)
    if not m:
        return None
    year, rest = int(m.group(1)), h[m.end():]
    d = DATE_RX.search(rest)
    if d:
        month, d1, d2 = MONTHS[d.group(1)], int(d.group(2)), int(d.group(3) or d.group(2))
        head, place = rest[:d.start()], rest[d.end():]
    else:
        month, d1, d2, head, place = 1, 1, 1, rest, ""
    cut = head.rfind(". ")
    title, venue = (head[:cut], head[cut + 2:]) if cut > 0 else (head, "")
    place = re.sub(r",?\s*USA\.?\s*$", "", place.strip()).rstrip(".")
    date = dt.date(year, month, d2)
    shown = (f"{d1}–{d2}" if d2 != d1 else f"{d1}") + f"\u00a0{MON3[month]} {year}"
    meta_parts = [kind, venue.strip().rstrip(".")]
    if place and place.split(",")[0].strip() not in venue:
        meta_parts[-1] += ", " + place
    title = title.strip().rstrip(".")
    return dict(date=date.isoformat(), shown=shown, title=title[0].upper() + title[1:],
                meta=" · ".join(p for p in meta_parts if p))


def parse_talks(tex):
    talks = []
    lead = section(tex, r"Conferences.*Lead")
    for head, body in subsections(lead):
        kind = "Oral presentation" if "oral" in head.lower() else "Poster"
        talks += [parse_talk(r, kind) for r in cvitems(body)]
    n_lead = len(talks)
    contrib = section(tex, r"Contributing")
    for head, body in subsections(contrib) or [("Poster", contrib)]:
        kind = ("Oral presentation" if "oral" in head.lower() else "Poster") + ", co-author"
        talks += [parse_talk(r, kind) for r in cvitems(body)]
    n_conf = len(talks)
    # invited talks: "\me (Month D, YYYY). Title. Kind, Host."
    inv = strip_comments(section(tex, r"Invited"))
    for line in [l for l in re.split(r"\\par|\n\s*\n", inv) if l.strip()]:
        h = to_html(line)
        m = re.search(r"\((" + "|".join(MONTHS) + r")\s+(\d{1,2}),\s*(\d{4})\)\.\s*(.*)", h)
        if not m:
            continue
        month, day, year, rest = MONTHS[m.group(1)], int(m.group(2)), int(m.group(3)), m.group(4)
        title, _, kindhost = rest.partition(". ")
        kind, _, host = kindhost.rstrip(". ").partition(", ")
        talks.append(dict(date=dt.date(year, month, day).isoformat(),
                          shown=f"{day}\u00a0{MON3[month]} {year}", title=title.strip(),
                          meta=" · ".join(p for p in (kind.strip(), host.strip()) if p)))
    talks = [t for t in talks if t]
    return talks, n_conf, n_lead


def yr_items(body):
    out = []
    for text, year in find_cmd(body, "yr", 2):
        out.append((to_html(text, bold=False).rstrip(" ."), to_html(year).replace(",", ", ").replace("  ", " ")))
    return out


def years_of(date):
    ys = re.findall(r"(?:19|20)\d{2}", date)
    if not ys:
        return to_html(date)
    if re.search(r"ongoing|present|now", date, re.I):
        return f"{ys[0]}–now"
    return ys[0] if len(set(ys)) == 1 else f"{ys[0]}–{ys[-1]}"


def parse_awards(tex):
    groups = {}
    for head, body in subsections(section(tex, r"^Awards")):
        groups[head.lower()] = yr_items(body)
    lead = []
    for title, _loc, _desc, date in find_cmd(section(tex, r"Leadership"), "cventryS", 4):
        lead.append((to_html(title, bold=False), years_of(date)))
    academic = next((v for k, v in groups.items() if "academic" in k), [])
    industry = next((v for k, v in groups.items() if "industry" in k), [])
    athletics = next((v for k, v in groups.items() if "athlet" in k or "sport" in k), [])
    sport_lead = [x for x in lead if re.search(r"badminton", x[0], re.I)]
    service = [x for x in lead if x not in sport_lead]
    return academic, industry, service, athletics + sport_lead


def parse_students(tex):
    out = []
    for head, body in subsections(section(tex, r"Advising")):
        tag = " (M.S., co-supervised)" if re.search(r"master", head, re.I) else ""
        for text, year in find_cmd(body, "yr", 2):
            b = re.search(r"\\textbf\{", text)
            title = balanced(text, b.end() - 1)[0] if b else text
            t = to_html(title, bold=False).rstrip(".")
            out.append((year.strip(), t + tag))
    return sorted(out, key=lambda x: x[0], reverse=True)  # newest first, stable


def parse_counts(tex):
    stats = {plain(b): plain(a) for a, b in find_cmd(tex, "stat", 2)}
    return stats


# ---------------------------------------------------------------- renderers
def li_pub(p):
    return (f'      <li class="pub" data-topic="{p["topic"]}">\n'
            f'        <span class="pub__year">{p["year"]}</span>\n'
            f'        <div><p class="pub__title">{p["title"]}</p>\n'
            f'        <p class="pub__meta">{p["meta"]}</p></div>\n'
            f'      </li>')


def render_pubs(pubs):
    parts = []
    first = True
    for key, label, attr in (("review", "Under review", " reversed"), ("published", "Published", "")):
        if not pubs[key]:
            continue
        cls = "pubs__group pubs__group--first" if first else "pubs__group"
        first = False
        parts.append(f'<h3 class="{cls}">{label}</h3>\n    <ol class="pubs"{attr}>\n'
                     + "\n".join(li_pub(p) for p in pubs[key]) + "\n    </ol>")
    return "\n\n    ".join(parts) + "\n    "


def num_word(n, one, many):
    return f"{n} {one if n == 1 else many}"


def render_talks(talks, today):
    up = sorted([t for t in talks if t["date"] >= today], key=lambda t: t["date"])
    past = sorted([t for t in talks if t["date"] < today], key=lambda t: t["date"], reverse=True)

    def li(t):
        return (f'      <li class="talk" data-date="{t["date"]}">\n'
                f'        <p class="talk__date">{t["shown"]}</p>\n'
                f'        <div><p class="talk__title">{t["title"]}</p>\n'
                f'        <p class="talk__meta">{t["meta"]}</p></div>\n'
                f'      </li>')
    hid = "" if up else " hidden"
    return (f'<h3 class="talks__group" id="talks-upcoming-title"{hid}>Coming up</h3>\n'
            f'    <ul class="talks talks--upcoming" aria-labelledby="talks-upcoming-title"{hid}>\n'
            + "\n".join(li(t) for t in up) + "\n    </ul>\n\n"
            f'    <h3 class="talks__group" id="talks-past-title">Earlier</h3>\n'
            f'    <ul class="talks talks--past" aria-labelledby="talks-past-title">\n'
            + "\n".join(li(t) for t in past) + "\n    </ul>\n    ")


def render_list(items):
    return "\n".join(f'          <li>{t} <span class="yr">{y}</span></li>' for t, y in items)


def render_awards(academic, industry, service, sport):
    def col(blocks):
        inner = []
        for i, (title, items) in enumerate(blocks):
            if not items:
                continue
            cls = ' class="col__sub"' if inner else ""
            inner.append(f'        <h3{cls}>{title}</h3>\n        <ul class="plain">\n{render_list(items)}\n        </ul>')
        return '\n      <div class="col reveal">\n' + "\n".join(inner) + "\n      </div>" if inner else ""
    return (col([("Academic", academic)]) + col([("Industry", industry), ("Service", service)])
            + col([("Badminton", sport)]))


def render_students(students):
    return "\n" + "\n".join(f"          <li><span>{y}</span>{t}</li>" for y, t in students) + "\n        "


# ---------------------------------------------------------------- main
def replace_region(page, name, new):
    rx = re.compile(r"(<!-- AUTO:" + name + r" -->)(.*?)(<!-- /AUTO:" + name + r" -->)", re.S)
    if not rx.search(page):
        raise SystemExit(f"marker AUTO:{name} not found in index.html")
    return rx.sub(lambda m: m.group(1) + new + m.group(3), page, count=1)


def region(page, name):
    m = re.search(r"<!-- AUTO:" + name + r" -->(.*?)<!-- /AUTO:" + name + r" -->", page, re.S)
    return m.group(1) if m else ""


def find_tex(path):
    p = pathlib.Path(path)
    if p.is_file():
        return p
    cands = [f for f in p.rglob("*.tex") if r"\begin{document}" in f.read_text(errors="ignore")]
    if len(cands) != 1:
        raise SystemExit(f"expected exactly one main .tex in {p}, found: {[str(c) for c in cands]}")
    return cands[0]


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    tex = strip_comments(find_tex(argv[1]).read_text(encoding="utf-8"))
    index = pathlib.Path(argv[2])
    page = index.read_text(encoding="utf-8")
    allow_fewer = "--allow-fewer" in argv
    today = dt.date.today().isoformat()

    pubs = parse_publications(tex)
    talks, n_conf, n_lead = parse_talks(tex)
    academic, industry, service, sport = parse_awards(tex)
    students = parse_students(tex)

    n_pub, n_rev = len(pubs["published"]), len(pubs["review"])
    problems = []
    if n_pub + n_rev == 0: problems.append("no publications found")
    if not talks: problems.append("no talks found")
    if not academic: problems.append("no academic awards found")
    if not students: problems.append("no supervised students found")
    if any(not p["title"] for k in pubs for p in pubs[k]): problems.append("a publication has no title")
    old_pubs = region(page, "pubs-list").count('class="pub"')
    old_talks = region(page, "talks-lists").count('class="talk"')
    if not allow_fewer and n_pub + n_rev < old_pubs:
        problems.append(f"publications dropped from {old_pubs} to {n_pub + n_rev}")
    if not allow_fewer and len(talks) < old_talks:
        problems.append(f"talks dropped from {old_talks} to {len(talks)}")
    if problems:
        print("NOT UPDATING the website:\n  - " + "\n  - ".join(problems))
        return 1

    pub_intro = (f'<p class="reveal">{num_word(n_pub, "peer-reviewed journal article", "peer-reviewed journal articles")}'
                 + (f' and {num_word(n_rev, "manuscript", "manuscripts")} under review' if n_rev else "")
                 + '. An asterisk marks the corresponding author. The full record is on '
                 '<a href="https://scholar.google.com/citations?hl=en&amp;user=_oGqy9IAAAAJ" rel="noopener">Google&nbsp;Scholar</a>.</p>')
    venues = []
    for t in talks:
        v = t["meta"]
        for name, short in (("IFT", "IFT"), ("Cereals", "the Cereals &amp; Grains Association"),
                            ("Kansas State", "Kansas State University")):
            if name in v and short not in venues:
                venues.append(short)
    where = (" at " + (", ".join(venues[:-1]) + " and " + venues[-1] if len(venues) > 1 else venues[0])) if venues else ""
    talks_intro = (f'<p class="talks__intro reveal">{n_conf} conference presentations, {n_lead} as lead author{where}.</p>')

    new = page
    new = replace_region(new, "pubs-intro", pub_intro)
    new = replace_region(new, "pubs-count", f'<p class="pubs__count" id="pubs-count" aria-live="polite">Showing all {n_pub + n_rev}</p>')
    new = replace_region(new, "pubs-list", render_pubs(pubs))
    new = replace_region(new, "talks-intro", talks_intro)
    new = replace_region(new, "talks-lists", render_talks(talks, today))
    new = replace_region(new, "awards", render_awards(academic, industry, service, sport) + "\n      ")
    new = replace_region(new, "students", render_students(students))

    print(f"Parsed: {n_pub} published, {n_rev} under review, {len(talks)} talks "
          f"({n_conf} conference, {n_lead} lead), {len(academic)}+{len(industry)} awards, "
          f"{len(service)} service, {len(sport)} badminton, {len(students)} students.")
    if new == page:
        print("No changes.")
        return 0
    if "--check" in argv:
        print("Changes found (check mode, not written).")
        return 0
    index.write_text(new, encoding="utf-8")
    print("index.html updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
