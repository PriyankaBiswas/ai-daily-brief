#!/usr/bin/env python3
import json
import html
from datetime import date, timedelta
from collections import defaultdict

REPO_ROOT = __file__.rsplit('/scripts/', 1)[0]
HISTORY_PATH = REPO_ROOT + '/data/history.json'
OUTPUT_PATH = REPO_ROOT + '/index.html'

MONTH_ABBR = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTH_FULL = ['', 'January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
WEEKDAY_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
WEEKDAY_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def e(s):
    return html.escape(str(s), quote=True)


def parse_date(s):
    y, m, d = s.split('-')
    return date(int(y), int(m), int(d))


def full_date_heading(d):
    return f"{WEEKDAY_FULL[d.weekday()]}, {MONTH_FULL[d.month]} {d.day}, {d.year}"


def short_day_summary(d):
    return f"{WEEKDAY_ABBR[d.weekday()]}, {MONTH_ABBR[d.month]} {d.day}"


def week_label(start, end):
    if start.month == end.month:
        return f"Week of {MONTH_ABBR[start.month]} {start.day} – {end.day}"
    return f"Week of {MONTH_ABBR[start.month]} {start.day} – {MONTH_ABBR[end.month]} {end.day}"


def render_reading_list(items):
    rows = []
    for it in items:
        badges = f'<span class="badge badge-mono">{e(it.get("minutes", "?"))} min</span>'
        if it.get('skip_ok'):
            badges += '<span class="badge badge-skip">skip ok</span>'
        rows.append(f'''
        <li class="item">
          <div class="item-head">
            <a class="item-title" href="{e(it.get('url', '#'))}" target="_blank" rel="noopener">{e(it.get('title', ''))}</a>
            {badges}
          </div>
          <div class="item-source">{e(it.get('source', ''))}</div>
          <p class="item-why">{e(it.get('why', ''))}</p>
        </li>''')
    return f'<ol class="reading-list">{"".join(rows)}</ol>'


def render_quiz(quiz):
    rows = []
    answer_rows = []
    for i, q in enumerate(quiz, 1):
        choices_html = ''
        if q.get('choices'):
            lis = ''.join(f'<li>{e(c)}</li>' for c in q['choices'])
            choices_html = f'<ul class="quiz-choices">{lis}</ul>'
        rows.append(f'''
        <li class="quiz-q">
          <p class="quiz-question">{e(q.get('q', ''))}</p>
          {choices_html}
        </li>''')
        answer_rows.append(f'<li><span class="quiz-q-num">{i}.</span> {e(q.get("a", ""))}</li>')
    quiz_html = f'<ol class="quiz-list">{"".join(rows)}</ol>'
    answers_html = f'''
    <details class="answers">
      <summary>\U0001F512 Answers</summary>
      <ol class="answer-list">{"".join(answer_rows)}</ol>
    </details>'''
    return quiz_html + answers_html


def render_build(build):
    if build is None:
        return '<p class="build-pending">Build idea lands at 11:30am</p>'
    plan_rows = ''.join(
        f'''<li><span class="plan-step">{e(step.get("step", ""))}</span>
            <span class="badge badge-mono">{e(step.get("minutes", "?"))} min</span></li>'''
        for step in build.get('plan', [])
    )
    tools_html = ''
    if build.get('tools'):
        tools_html = f'''
        <div class="build-field">
          <h4>Tools</h4>
          <ul class="tools-list">{"".join(f"<li>{e(t)}</li>" for t in build['tools'])}</ul>
        </div>'''
    stretch_html = ''
    if build.get('stretch_goal'):
        stretch_html = f'''
        <div class="build-field">
          <h4>Stretch goal</h4>
          <p>{e(build['stretch_goal'])}</p>
        </div>'''
    return f'''
    <div class="build-card">
      <div class="build-head">
        <span class="badge badge-category">{e(build.get('category', ''))}</span>
      </div>
      <p class="build-pitch">{e(build.get('pitch', ''))}</p>
      <div class="build-field">
        <h4>Why</h4>
        <p>{e(build.get('why', ''))}</p>
      </div>
      <div class="build-field">
        <h4>Plan</h4>
        <ol class="plan-list">{plan_rows}</ol>
      </div>
      <div class="build-field">
        <h4>Done looks like</h4>
        <p>{e(build.get('done_looks_like', ''))}</p>
      </div>
      {stretch_html}
      {tools_html}
    </div>'''


def render_day_content(record):
    reading = record.get('reading', {})
    parts = []
    intro = reading.get('intro')
    if intro:
        parts.append(f'<p class="day-intro">{e(intro)}</p>')
    parts.append('<h3 class="section-label">Today’s reading list</h3>' if False else '<h3 class="section-label">Reading list</h3>')
    parts.append(render_reading_list(reading.get('items', [])))
    parts.append('<h3 class="section-label">Recall quiz</h3>')
    parts.append(render_quiz(reading.get('quiz', [])))
    parts.append('<h3 class="section-label">Build idea</h3>')
    parts.append(render_build(record.get('build')))
    return f'<div class="day-content">{"".join(parts)}</div>'


def build_archive_tree(records):
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for rec in records:
        d = parse_date(rec['date'])
        week_start = d - timedelta(days=d.weekday())
        tree[week_start.year][week_start.month][week_start].append((d, rec))
    return tree


def render_archive(records):
    if not records:
        return ''
    tree = build_archive_tree(records)
    years_html = []
    for year in sorted(tree.keys(), reverse=True):
        months_html = []
        for month in sorted(tree[year].keys(), reverse=True):
            weeks_html = []
            week_starts = sorted(tree[year][month].keys(), reverse=True)
            for week_start in week_starts:
                day_list = sorted(tree[year][month][week_start], key=lambda t: t[0], reverse=True)
                week_end = week_start + timedelta(days=6)
                days_html = []
                for d, rec in day_list:
                    days_html.append(f'''
                    <details class="day-entry">
                      <summary>{short_day_summary(d)}</summary>
                      {render_day_content(rec)}
                    </details>''')
                weeks_html.append(f'''
                <details class="week-entry">
                  <summary>{week_label(week_start, week_end)}</summary>
                  {"".join(days_html)}
                </details>''')
            months_html.append(f'''
            <details class="month-entry">
              <summary>{MONTH_FULL[month]}</summary>
              {"".join(weeks_html)}
            </details>''')
        years_html.append(f'''
        <details class="year-entry">
          <summary>{year}</summary>
          {"".join(months_html)}
        </details>''')
    return f'''
    <details class="archive-root">
      <summary>Archive</summary>
      <div class="archive-tree">{"".join(years_html)}</div>
    </details>'''


PAGE_TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Daily Brief</title>
<meta name="description" content="Pri's daily AI reading list, recall quiz, and build idea.">
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Work+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
  --bg: #FAF8F4;
  --surface: #FFFFFF;
  --text: #1c1c1e;
  --muted: #6b6b70;
  --border: #e6e4e0;
  --accent: #6D4AFF;
  --accent-soft: #EFE9FF;
  --good: #1a7f5a;
}}

@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #17161c;
    --surface: #201f27;
    --text: #efeef2;
    --muted: #a3a1ab;
    --border: #35333e;
    --accent: #a992ff;
    --accent-soft: #2c2640;
    --good: #4fcf9d;
  }}
}}

:root[data-theme="dark"] {{
  --bg: #17161c;
  --surface: #201f27;
  --text: #efeef2;
  --muted: #a3a1ab;
  --border: #35333e;
  --accent: #a992ff;
  --accent-soft: #2c2640;
  --good: #4fcf9d;
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: 'Work Sans', sans-serif;
  line-height: 1.6;
}}

.wrap {{
  max-width: 780px;
  margin: 0 auto;
  padding: 48px 16px 96px;
}}

header.site-header {{
  margin-bottom: 48px;
}}

header.site-header h1 {{
  font-family: 'Fraunces', serif;
  font-size: 2.6rem;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: -0.01em;
}}

header.site-header p.tagline {{
  margin: 0;
  color: var(--muted);
  font-size: 1.05rem;
}}

h2.day-heading {{
  font-family: 'Fraunces', serif;
  font-size: 1.9rem;
  font-weight: 600;
  margin: 0 0 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--border);
}}

section.today {{
  margin-bottom: 64px;
}}

.day-intro {{
  font-size: 1.05rem;
  color: var(--text);
  background: var(--accent-soft);
  border-radius: 12px;
  padding: 18px 20px;
  margin: 0 0 28px;
}}

h3.section-label {{
  font-family: 'Fraunces', serif;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 36px 0 16px;
}}

ol.reading-list {{
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: item-counter;
}}

li.item {{
  counter-increment: item-counter;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 12px;
  position: relative;
  padding-left: 52px;
}}

li.item::before {{
  content: counter(item-counter);
  position: absolute;
  left: 16px;
  top: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: var(--accent);
  font-weight: 500;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--accent-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}}

.item-head {{
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 4px;
}}

a.item-title {{
  font-family: 'Fraunces', serif;
  font-weight: 600;
  font-size: 1.08rem;
  color: var(--text);
  text-decoration: none;
  border-bottom: 1px solid var(--accent);
}}

a.item-title:hover {{
  color: var(--accent);
}}

.item-source {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 8px;
}}

p.item-why {{
  margin: 0;
  color: var(--text);
  font-size: 0.97rem;
}}

.badge {{
  display: inline-block;
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}}

.badge-mono {{
  font-family: 'JetBrains Mono', monospace;
  background: var(--accent-soft);
  color: var(--accent);
}}

.badge-skip {{
  font-family: 'Work Sans', sans-serif;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
}}

.badge-category {{
  font-family: 'JetBrains Mono', monospace;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.78rem;
  padding: 4px 10px;
}}

ol.quiz-list {{
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: quiz-counter;
}}

li.quiz-q {{
  counter-increment: quiz-counter;
  padding: 12px 0 12px 32px;
  border-bottom: 1px solid var(--border);
  position: relative;
}}

li.quiz-q:last-child {{
  border-bottom: none;
}}

li.quiz-q::before {{
  content: counter(quiz-counter) ".";
  position: absolute;
  left: 0;
  top: 12px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--muted);
  font-size: 0.9rem;
}}

p.quiz-question {{
  margin: 0 0 6px;
  font-weight: 500;
}}

ul.quiz-choices {{
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
}}

ul.quiz-choices li {{
  margin-bottom: 2px;
}}

details.answers {{
  margin-top: 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
}}

details.answers summary {{
  cursor: pointer;
  font-weight: 600;
  font-family: 'Fraunces', serif;
  font-size: 1.05rem;
}}

ol.answer-list {{
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
}}

ol.answer-list li {{
  padding: 6px 0;
  font-size: 0.95rem;
}}

.quiz-q-num {{
  font-family: 'JetBrains Mono', monospace;
  color: var(--accent);
  margin-right: 4px;
}}

.build-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 22px;
}}

.build-head {{
  margin-bottom: 10px;
}}

p.build-pitch {{
  font-family: 'Fraunces', serif;
  font-size: 1.15rem;
  font-weight: 500;
  margin: 0 0 18px;
}}

.build-field {{
  margin-bottom: 16px;
}}

.build-field h4 {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  margin: 0 0 6px;
}}

.build-field p {{
  margin: 0;
}}

ol.plan-list {{
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: plan-counter;
}}

ol.plan-list li {{
  counter-increment: plan-counter;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
}}

ol.plan-list li:last-child {{
  border-bottom: none;
}}

ol.plan-list li::before {{
  content: counter(plan-counter) ".";
  font-family: 'JetBrains Mono', monospace;
  color: var(--accent);
  margin-right: 8px;
}}

.plan-step {{
  flex: 1;
}}

ul.tools-list {{
  margin: 0;
  padding-left: 18px;
}}

p.build-pending {{
  color: var(--muted);
  font-style: italic;
  margin: 0;
}}

details.archive-root {{
  margin-top: 32px;
  border-top: 2px solid var(--border);
  padding-top: 24px;
}}

details.archive-root > summary {{
  font-family: 'Fraunces', serif;
  font-size: 1.6rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 8px;
}}

.archive-tree {{
  margin-top: 16px;
}}

details.year-entry, details.month-entry, details.week-entry {{
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  padding: 12px 16px;
  background: var(--surface);
}}

details.year-entry > summary {{
  font-family: 'Fraunces', serif;
  font-size: 1.3rem;
  font-weight: 600;
  cursor: pointer;
}}

details.month-entry > summary {{
  font-family: 'Fraunces', serif;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
}}

details.week-entry > summary {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: var(--muted);
  cursor: pointer;
}}

details.year-entry > .month-entry,
details.month-entry > .week-entry {{
  margin-top: 12px;
}}

details.day-entry {{
  border-top: 1px solid var(--border);
  margin-top: 10px;
  padding-top: 10px;
}}

details.day-entry > summary {{
  font-family: 'Fraunces', serif;
  font-weight: 600;
  cursor: pointer;
  font-size: 1rem;
}}

details.day-entry .day-content {{
  margin-top: 14px;
}}

summary {{
  list-style: none;
}}

summary::-webkit-details-marker {{
  display: none;
}}

summary::before {{
  content: '\\25B8';
  display: inline-block;
  margin-right: 8px;
  color: var(--accent);
  transition: transform 0.15s ease;
}}

details[open] > summary::before {{
  transform: rotate(90deg);
}}

@media (max-width: 480px) {{
  header.site-header h1 {{ font-size: 2.1rem; }}
  h2.day-heading {{ font-size: 1.5rem; }}
  li.item {{ padding-left: 44px; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header class="site-header">
    <h1>AI Daily Brief</h1>
    <p class="tagline">A ranked reading list, a recall quiz, and a build idea — every day.</p>
  </header>

  <section class="today">
    <h2 class="day-heading">{today_heading}</h2>
    {today_content}
  </section>

  {archive_html}
</div>
</body>
</html>
'''


def main():
    with open(HISTORY_PATH) as f:
        history = json.load(f)

    records_by_date = {r['date']: r for r in history}
    today_date_str = max(records_by_date.keys())
    today_record = records_by_date[today_date_str]
    today_d = parse_date(today_date_str)

    archive_records = [r for r in history if r['date'] != today_date_str]

    html_out = PAGE_TEMPLATE.format(
        today_heading=full_date_heading(today_d),
        today_content=render_day_content(today_record),
        archive_html=render_archive(archive_records),
    )

    with open(OUTPUT_PATH, 'w') as f:
        f.write(html_out)

    print(f"Wrote {OUTPUT_PATH} ({len(html_out)} bytes), today={today_date_str}, archive_days={len(archive_records)}")


if __name__ == '__main__':
    main()
