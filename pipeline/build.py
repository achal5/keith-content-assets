#!/usr/bin/env python3
"""Build Keith's carousel + story PNGs from a JSON spec.

Usage:  python3 build.py spec.json OUTDIR
Needs:  npm install (in this folder, for fonts) and python playwright with Chromium
        (PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers, executable /opt/pw-browsers/chromium).
See ../RUNBOOK.md for the spec format. Images referenced in the spec are paths
relative to the spec file's folder (or absolute).
"""
import asyncio, html, json, pathlib, re, sys
from playwright.async_api import async_playwright

BASE = pathlib.Path(__file__).parent.resolve()
BLUE, YEL, ORG, GREY = "#0070cd", "#f8d53a", "#fb7d25", "#5c636b"

ICONS = {
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "carousel": '<rect x="7" y="4" width="11" height="16" rx="2.5"/><path d="M4 7v10M21 7v10"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "trend": '<path d="M4 4v16h16"/><path d="M8 9l4 4 3-3 4 5"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "play": '<path d="M7 4l13 8-13 8z"/>',
    "megaphone": '<path d="M3 11v2a1 1 0 0 0 1 1h3l8 4V6L7 10H4a1 1 0 0 0-1 1z"/><path d="M19 8a5 5 0 0 1 0 8"/>',
}

def esc(s): return html.escape(str(s), quote=False)

def hl(text, pad=14):
    """Text with [[highlighted words]] -> HTML with yellow highlight span."""
    out = ""
    for part in re.split(r"(\[\[.*?\]\])", str(text)):
        if part.startswith("[[") and part.endswith("]]"):
            out += ('<span style="background:#f8d53a;color:#0070cd;padding:2px %dpx;box-decoration-break:clone;'
                    '-webkit-box-decoration-break:clone">%s</span>' % (pad, esc(part[2:-2])))
        else:
            out += esc(part)
    return out

def tex(w, h, dark):
    if dark:
        return (f'<svg aria-hidden="true" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="position:absolute;left:0;top:0;z-index:-1;pointer-events:none"><filter id="mottleB" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.02" numOctaves="3" seed="7"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0.12  0 0 0 0 0.35  2.6 0 0 0 -1.2"/></filter><filter id="specksB" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="11"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  7 0 0 0 -4.4"/></filter><rect width="{w}" height="{h}" filter="url(#mottleB)" opacity=".35"/><rect width="{w}" height="{h}" filter="url(#specksB)" opacity=".28"/></svg>')
    return (f'<svg aria-hidden="true" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="position:absolute;left:0;top:0;z-index:-1;pointer-events:none"><filter id="mottleL" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.02" numOctaves="3" seed="7"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0.44  0 0 0 0 0.8  2.2 0 0 0 -1.0"/></filter><filter id="specksL" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="11"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0.44  0 0 0 0 0.8  7 0 0 0 -4.4"/></filter><rect width="{w}" height="{h}" filter="url(#mottleL)" opacity=".08"/><rect width="{w}" height="{h}" filter="url(#specksL)" opacity=".14"/></svg>')

def rings(w, top=True):
    a = "right:-300px;top:-300px;width:900px;height:900px" if top else "left:-300px;bottom:-300px;width:900px;height:900px"
    b = "right:-160px;top:-160px;width:620px;height:620px" if top else "left:-160px;bottom:-160px;width:620px;height:620px"
    s = "position:absolute;%s;border-radius:50%%;border:2px solid rgba(255,255,255,.16)"
    return f'<div aria-hidden="true" style="{s % a}"></div><div aria-hidden="true" style="{s % b}"></div>'

def frame(w, h, bg, dark, inner, pad="72px", gap=None, justify=None):
    g = f"gap:{gap}px;" if gap else ""
    j = f"justify-content:{justify};" if justify else ""
    return (f'<div id="art" style="width:{w}px;height:{h}px;position:relative;overflow:hidden;box-sizing:border-box;background:{bg};'
            f"font-family:'Montserrat',sans-serif;padding:{pad};display:flex;flex-direction:column;{j}{g}isolation:isolate\">"
            f"{tex(w, h, dark)}{inner}</div>")

def chip(text, bg, fg, size=24, pad="10px 24px"):
    return (f'<span style="display:inline-flex;align-self:flex-start;background:{bg};color:{fg};font-weight:700;font-size:{size}px;'
            f'letter-spacing:.14em;text-transform:uppercase;padding:{pad};border-radius:999px">{esc(text)}</span>')

def h2(text, size, color, pad=14, line=1.16, extra=""):
    return (f"<h2 style=\"margin:0;font-family:'Montserrat',sans-serif;font-weight:800;font-size:{size}px;line-height:{line};"
            f'letter-spacing:-.01em;text-transform:uppercase;color:{color};text-wrap:balance;{extra}">{hl(text, pad)}</h2>')

def sub(text, size, color, maxw=900):
    return (f"<p style=\"margin:0;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:{size}px;line-height:1.2;"
            f'letter-spacing:.02em;color:{color};max-width:{maxw}px;text-wrap:pretty">{esc(text)}</p>')

def logo(dark, h=56):
    return f'<img src="assets/logo-mark{"-white" if dark else ""}.png" alt="Sociallyin" style="height:{h}px">'

def header(n, total, dark):
    col = "#ffffff" if dark else BLUE
    return (f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between">{logo(dark)}'
            f'<span style="font-weight:700;font-size:24px;letter-spacing:.06em;color:{col}">{n} / {total}</span></div>')

def squiggle(extra=""):
    return ('<svg aria-hidden="true" width="300" height="18" viewBox="0 0 300 18" fill="none" style="%s"><path d="M4 10Q29 0 54 10T104 10T154 10T204 10T254 10T296 10" stroke="#fb7d25" stroke-width="6" stroke-linecap="round"/></svg>' % extra)

def img_src(p, root):
    p = pathlib.Path(p)
    if not p.is_absolute(): p = (root / p).resolve()
    return "file://" + str(p)

# ---------------- carousel slides (1080 x 1350) ----------------
def s_cover(s, n, total, ctx):
    inner = (f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between">{logo(True)}'
             f'<span style="font-weight:700;font-size:26px;color:#fff">@keithsol</span></div>'
             f'<div style="display:flex;flex-direction:column;align-items:center;gap:56px">'
             f"<h1 style=\"margin:0;font-family:'Montserrat',sans-serif;font-weight:800;font-size:{s.get('size',108)}px;line-height:1.06;letter-spacing:-.01em;text-transform:uppercase;text-align:center;color:#fff;text-wrap:balance\">{esc(s['hook'])}</h1>"
             f'<div style="transform:rotate(-3deg);max-width:900px;text-align:center"><span style="display:inline;background:#f8d53a;color:#0070cd;'
             f"font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:76px;line-height:1.28;letter-spacing:.01em;padding:6px 24px;box-decoration-break:clone;-webkit-box-decoration-break:clone\">{esc(s['label'])}</span></div></div>"
             f'<div style="display:flex;align-items:center;justify-content:space-between"><span style="font-weight:700;font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#fff">Social media news · {esc(s["date"])}</span>'
             f"<span style=\"display:inline-flex;align-items:center;gap:12px;background:#fff;color:#0070cd;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:40px;letter-spacing:.04em;padding:10px 28px;border-radius:999px\">Swipe"
             f'<svg aria-hidden="true" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0070cd" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></svg></span></div>')
    return frame(1080, 1350, BLUE, True, inner, justify="space-between")

def s_stat(s, n, total, ctx):
    inner = (rings(1080) + header(n, total, True) +
             '<div style="position:relative;display:flex;flex-direction:column;gap:20px">' + chip(s["tag"], "#fff", BLUE) +
             f"<div style=\"font-family:'Montserrat',sans-serif;font-weight:900;font-size:{s.get('number_size',210)}px;line-height:1;letter-spacing:-.03em;color:#fff\">{esc(s['number'])}</div>" +
             h2(s["headline"], 60, "#fff", line=1.18) + squiggle("margin-top:4px") + sub(s["sub"], 48, "#fff") + "</div>" +
             f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between"><span style="font-weight:500;font-size:22px;color:#fff">Source: {esc(s["source"])}</span>'
             f"<span style=\"font-family:'Bebas Neue',sans-serif;font-size:32px;letter-spacing:.04em;color:#f8d53a\">@keithsol</span></div>")
    return frame(1080, 1350, BLUE, True, inner, justify="space-between")

def s_news(s, n, total, ctx):
    pale = s.get("bg", "pale" if ctx["news_i"] % 2 == 0 else "white") == "pale"
    bg = "#eef6fc" if pale else "#ffffff"
    h = s.get("image_h", 380)
    fit = s.get("fit", "cover")
    ibg = s.get("image_bg", "#0a0c0f")
    icon = ICONS[s.get("icon", "bolt")]
    border = "" if pale else "border:1px solid #dce0e4;"
    inner = (header(n, total, False) +
             '<div style="display:flex;flex-direction:column;gap:20px">' + chip(s["tag"], BLUE, "#fff") +
             h2(s["headline"], s.get("size", 72), BLUE) + sub(s["sub"], 46, GREY) + "</div>" +
             '<div style="position:relative;margin-top:auto">'
             '<div style="position:absolute;right:-8px;top:-44px;z-index:2;width:120px;height:120px;border-radius:50%;background:#f8d53a;display:flex;align-items:center;justify-content:center;transform:rotate(8deg);box-shadow:0 10px 24px rgba(16,25,45,.14)">'
             f'<svg role="img" width="68" height="68" viewBox="0 0 24 24" fill="none" stroke="#0070cd" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></div>'
             f'<div style="background:#fff;border-radius:24px;padding:24px;box-shadow:0 22px 48px rgba(16,25,45,.14);{border}display:flex;flex-direction:column;gap:16px">'
             f'<div style="height:{h}px;border-radius:16px;overflow:hidden;background:{ibg}"><img src="{img_src(s["image"], ctx["root"])}" alt="" style="display:block;width:100%;height:100%;object-fit:{fit}"></div>'
             f'<div style="display:flex;align-items:center;justify-content:space-between"><span style="font-weight:500;font-size:22px;color:{GREY}">Source: {esc(s["source"])}</span>'
             f"<span style=\"font-family:'Bebas Neue',sans-serif;font-size:30px;letter-spacing:.04em;color:#0070cd\">@keithsol</span></div></div></div>")
    ctx["news_i"] += 1
    return frame(1080, 1350, bg, False, inner, gap=28)

def s_take(s, n, total, ctx):
    por = s.get("portrait", "IMG_9255.jpg")
    inner = (header(n, total, False) +
             '<div style="display:flex;flex-direction:column;gap:20px">' + chip(s.get("tag", "My take"), YEL, BLUE) +
             h2(s["headline"], 78, BLUE) + sub(s["sub"], 46, GREY) + "</div>" +
             '<div style="position:relative;margin-top:auto;height:440px;border-radius:24px;overflow:hidden;background:#0070cd;box-shadow:0 22px 48px rgba(16,25,45,.14)">'
             f'<img src="assets/portraits/{por}" alt="Keith Kakadia" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 14%">'
             '<div style="position:absolute;left:24px;bottom:24px;display:flex;align-items:center;gap:16px;background:#fff;border-radius:999px;padding:12px 28px 12px 14px;box-shadow:0 10px 24px rgba(16,25,45,.14)">'
             '<img src="assets/logo-mark.png" alt="" style="height:40px"><div style="display:flex;flex-direction:column;gap:2px">'
             "<span style=\"font-family:'Bebas Neue',sans-serif;font-size:34px;letter-spacing:.02em;color:#0070cd;line-height:1\">Keith Kakadia</span>"
             '<span style="font-weight:600;font-size:18px;color:#5c636b">Founder &amp; CEO, Sociallyin</span></div></div></div>')
    return frame(1080, 1350, "#ffffff", False, inner, gap=28)

def s_cta(s, n, total, ctx):
    inner = (rings(1080, top=False) + header(n, total, True) +
             '<div style="position:relative;display:flex;flex-direction:column;gap:22px">' + chip(s.get("tag", "Your turn"), "#fff", BLUE) +
             h2(s["headline"], 84, "#fff", pad=16) + sub(s["sub"], 46, "#fff") + "</div>" +
             '<div style="position:relative;margin-top:auto;display:flex;flex-direction:column;gap:22px">'
             '<div style="background:#fff;border-radius:24px;padding:26px 28px;box-shadow:0 22px 48px rgba(16,25,45,.2);display:flex;align-items:center;gap:20px">'
             '<span style="width:60px;height:60px;border-radius:50%;background:#cde4f1;display:inline-flex;align-items:center;justify-content:center;flex:none"><img src="assets/logo-mark.png" alt="" style="height:32px"></span>'
             f'<div style="display:flex;flex-direction:column;gap:6px;flex:1"><span style="font-weight:700;font-size:22px;color:#0070cd">@yourhandle</span><span style="font-weight:600;font-size:30px;color:#5c636b">{esc(s["keyword"])}</span></div>'
             '<svg aria-hidden="true" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#0070cd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-4.5-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z"/></svg></div>'
             '<div style="display:flex;align-items:center;justify-content:space-between">'
             "<span style=\"display:inline-flex;align-items:center;background:#fff;color:#0070cd;font-family:'Bebas Neue',sans-serif;font-size:38px;letter-spacing:.04em;padding:12px 34px;border-radius:999px\">Follow @keithsol for weekly social news</span>"
             "<span style=\"font-family:'Bebas Neue',sans-serif;font-size:44px;letter-spacing:.04em;color:#f8d53a\">Are you in?</span></div></div>")
    return frame(1080, 1350, BLUE, True, inner, gap=30)

# ---------------- stories (1080 x 1920, 250px safe zones) ----------------
def story_quick(s, ctx):
    num = ""
    if s.get("number"):
        size = s.get("number_size", 240 if len(s["number"]) <= 6 else 200)
        num = f"<div style=\"font-family:'Montserrat',sans-serif;font-weight:900;font-size:{size}px;line-height:1;letter-spacing:-.03em;color:#0070cd\">{esc(s['number'])}</div>"
    src = f'<p style="margin:0;font-weight:500;font-size:24px;color:#5c636b">Source: {esc(s["source"])}</p>' if s.get("source") else ""
    inner = (f'<div style="display:flex;align-items:center;justify-content:space-between">{chip(s.get("chip", "Quick take"), BLUE, "#fff", 26, "12px 26px")}{logo(False, 52)}</div>'
             '<div style="display:flex;flex-direction:column;gap:24px">' + num +
             h2(s["headline"], s.get("size", 76), BLUE) + squiggle() + sub(s["sub"], 52, GREY, 936) + src + "</div>"
             '<div style="display:flex;align-items:center;gap:22px;background:#eef6fc;border-radius:999px;padding:16px 34px 16px 16px;align-self:flex-start">'
             '<img src="assets/portraits/3B2A1394.jpg" alt="Keith Kakadia" style="width:84px;height:84px;border-radius:50%;object-fit:cover;object-position:50% 20%;box-shadow:0 0 0 3px #f8d53a">'
             "<div style=\"display:flex;flex-direction:column;gap:4px\"><span style=\"font-family:'Bebas Neue',sans-serif;font-size:38px;letter-spacing:.02em;color:#0070cd;line-height:1\">Keith Kakadia</span>"
             '<span style="font-weight:600;font-size:22px;color:#5c636b">@keithsol</span></div></div>')
    return frame(1080, 1920, "#ffffff", False, inner, pad="250px 72px", justify="space-between")

def story_news(s, ctx):
    fit, ibg = s.get("fit", "cover"), s.get("image_bg", "#0a0c0f")
    inner = (rings(1080) + f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between">{chip(s.get("chip", "Social news"), "#fff", BLUE, 26, "12px 26px")}</div>'
             '<div style="position:relative;display:flex;flex-direction:column;gap:34px">' + h2(s["headline"], 88, "#fff", pad=16) +
             f'<div style="background:#fff;border-radius:24px;padding:22px;box-shadow:0 22px 48px rgba(16,25,45,.2)"><div style="height:480px;border-radius:16px;overflow:hidden;background:{ibg}"><img src="{img_src(s["image"], ctx["root"])}" alt="" style="display:block;width:100%;height:100%;object-fit:{fit}"></div></div>' +
             sub(s["sub"], 52, "#fff", 936) + "</div>"
             f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between"><span style="font-weight:500;font-size:24px;color:#fff">Source: {esc(s["source"])}</span>{logo(True, 52)}</div>')
    return frame(1080, 1920, BLUE, True, inner, pad="250px 72px", justify="space-between")

def story_poll(s, ctx):
    inner = (f'<div style="display:flex;align-items:center;justify-content:space-between">{logo(False, 52)}{chip("Your call", BLUE, "#fff", 26, "12px 26px")}</div>'
             '<div style="display:flex;flex-direction:column;gap:34px">' + h2(s["headline"], 88, BLUE, pad=16) + sub(s["context"], 52, GREY, 936) +
             '<div style="background:#fff;border-radius:24px;padding:22px;box-shadow:0 22px 48px rgba(16,25,45,.14)"><div style="height:360px;border-radius:16px;background:#eef6fc"></div></div></div>'
             '<div style="display:flex;align-items:center;justify-content:space-between"><span style="font-weight:700;font-size:26px;color:#0070cd">@keithsol</span>'
             "<span style=\"font-family:'Bebas Neue',sans-serif;font-size:44px;letter-spacing:.04em;color:#0070cd\">Are you in?</span></div>")
    return frame(1080, 1920, "#eef6fc", False, inner, pad="250px 72px", justify="space-between")

SLIDES = {"stat": s_stat, "news": s_news, "take": s_take, "cta": s_cta}
STORIES = {"quick": story_quick, "news": story_news, "poll": story_poll}

def page(body):
    fonts = BASE / "node_modules/@fontsource"
    css = ""
    for w in (400, 500, 600, 700, 800, 900):
        css += "@font-face{font-family:'Montserrat';font-weight:%d;src:url('file://%s/montserrat/files/montserrat-latin-%d-normal.woff2') format('woff2')}\n" % (w, fonts, w)
    css += "@font-face{font-family:'Bebas Neue';font-weight:400;src:url('file://%s/bebas-neue/files/bebas-neue-latin-400-normal.woff2') format('woff2')}\nbody{margin:0}" % fonts
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"

async def main(spec_path, outdir):
    spec_path = pathlib.Path(spec_path).resolve()
    root = spec_path.parent
    spec = json.loads(spec_path.read_text())
    out = pathlib.Path(outdir).resolve(); out.mkdir(parents=True, exist_ok=True)
    ctx = {"root": root, "news_i": 0}
    jobs = []  # (filename, html, w, h)
    car = spec.get("carousel")
    if car:
        slides = [("cover", car["cover"])] + [(x.get("type", "news"), x) for x in car["slides"]]
        if car.get("take"): slides.append(("take", car["take"]))
        if car.get("cta"): slides.append(("cta", car["cta"]))
        total = len(slides)
        for i, (t, s) in enumerate(slides, 1):
            body = s_cover(s, i, total, ctx) if t == "cover" else SLIDES[t](s, i, total, ctx)
            jobs.append((f"slide-{i}.png", body, 1080, 1350))
    for i, s in enumerate(spec.get("stories", []), 1):
        name = s.get("name") or f"story-{i}"
        jobs.append((f"{name}.png", STORIES[s["type"]](s, ctx), 1080, 1920))
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--allow-file-access-from-files"])
        for fn, body, w, h in jobs:
            pg = await b.new_page(viewport={"width": w, "height": h})
            f = BASE / (".tmp-" + fn[:-4] + ".html")
            f.write_text(page(body))
            await pg.goto("file://" + str(f.resolve()))
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await (await pg.query_selector("#art")).screenshot(path=str(out / fn))
            await pg.close()
            f.unlink()
            print("built", fn)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
