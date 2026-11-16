import base64, io, os, sys
from fontTools.ttLib import TTFont
from fontTools import subset

FONT_DIR = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

W = 830
TEXT_LIGHT, TEXT_DARK = "#1f2328", "#e6edf3"
PURPLE = "#A256F8"
TITLE_LIGHT, TITLE_DARK = "#7C3AED", "#B794F6"

STYLES = {
    "body":    ("400", False, 15, "t"),
    "bold":    ("700", False, 15, "t"),
    "tagline": ("600", True, 16, "p"),
    "title":   ("700", False, 19, "h"),
}
FILES = {("400", False): "nunito-latin-400-normal.woff2",
         ("700", False): "nunito-latin-700-normal.woff2",
         ("600", True): "nunito-latin-600-italic.woff2"}
fonts = {k: TTFont(os.path.join(FONT_DIR, v)) for k, v in FILES.items()}


def width(text, weight, italic, size):
    f = fonts[(weight, italic)]
    cmap, hmtx, upem = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text) * size / upem


def wrap(runs):
    """runs: [(style, text)] -> lines of [(style, text)]"""
    words = []
    for style, text in runs:
        parts = text.split(" ")
        for i, p in enumerate(parts):
            words.append((style, p, i < len(parts) - 1 or text.endswith(" ")))
    lines, cur, x = [], [], 0.0
    for style, w, space_after in words:
        if not w:
            continue
        wt, it, sz, _ = STYLES[style]
        ww = width(w, wt, it, sz)
        sp = width(" ", wt, it, sz)
        if cur and x + ww > W:
            lines.append(cur); cur, x = [], 0.0
        cur.append((style, w)); x += ww + sp
    if cur:
        lines.append(cur)
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_face(chars_by_font):
    css = []
    for (wt, it), chars in chars_by_font.items():
        if not chars:
            continue
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]
        f = TTFont(os.path.join(FONT_DIR, FILES[(wt, it)]))
        s = subset.Subsetter(opts); s.populate(text="".join(sorted(chars)) + " ?"); s.subset(f)
        buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:'NunitoE';font-weight:{wt};font-style:{'italic' if it else 'normal'};"
                   f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "".join(css)


def render(name, blocks):
    """blocks: list of (gap_before, runs). runs = [(style, text)]."""
    y, out, chars = 0, [], {k: set() for k in FILES}
    for gap, runs in blocks:
        y += gap
        size = max(STYLES[s][2] for s, _ in runs)
        lh = round(size * 1.65)
        for line in wrap(runs):
            y += lh
            spans = []
            for i, (style, w) in enumerate(line):
                wt, it, sz, cls = STYLES[style]
                chars[(wt, it)].update(w)
                txt = esc(w) + (" " if i < len(line) - 1 else "")
                spans.append(f'<tspan class="{cls}" font-weight="{wt}" font-style="{"italic" if it else "normal"}" font-size="{sz}">{txt}</tspan>')
            out.append(f'<text x="0" y="{y - round(lh * 0.3)}" xml:space="preserve">{"".join(spans)}</text>')
    h = y + 6
    style = (font_face(chars) +
             f"text{{font-family:'NunitoE',Nunito,sans-serif}}"
             f".t{{fill:{TEXT_LIGHT}}}.p{{fill:{PURPLE}}}.h{{fill:{TITLE_LIGHT}}}"
             f"@media (prefers-color-scheme:dark){{.t{{fill:{TEXT_DARK}}}.h{{fill:{TITLE_DARK}}}}}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
           f"<style>{style}</style>{''.join(out)}</svg>")
    with open(os.path.join(OUT, name + ".svg"), "w") as fh:
        fh.write(svg)
    print(name, W, h, len(svg) // 1024, "KB")


B = lambda t: ("body", t)
S = lambda t: ("bold", t)
TAG = lambda t: ("tagline", t)
L, P = 6, 16

render("about", [
    (0, [B("I connect digital marketing with technology – from PPC campaigns and analytics to websites, automation and AI-powered tools.")]),
    (L, [B("3+ years of hands-on work with websites gave me a strong foundation in web technologies, analytics and tracking, so I don't stop at campaign settings – I look at the whole picture: the website, the data, the tracking setup and the user experience that drive results.")]),
    (L, [B("I work with both B2B and B2C businesses, from lead generation to e-commerce, combining data-driven decisions with creative, unconventional thinking.")]),
    (P, [B("I build my own open-source tools & SaaS projects.")]),
    (L, [B("I automate repetitive work with n8n, Zapier and other tools, with a little help from LLMs.")]),
    (L, [B("My experience also spans MarTech, social media and the streaming/esports industry, which gives me a broader view of how advertising, technology, content and user experience work together.")]),
    (P, [B("I enjoy solving problems where marketing, technology and creativity meet.")]),
    (P, [B("Outside of work, I'm into automation, SaaS and startups, video games and cars – especially Japanese ones.")]),
    (L, [B("In my free time I build games and all kinds of small programs just for fun.")]),
])

render("title-meowlearn", [(0, [("title", "MeowLearn")])])
render("title-conversion-toolkit", [(0, [("title", "Conversion Toolkit")])])
render("title-chrome-extension", [(0, [("title", "Chrome Extension – Conversion Toolkit")])])

render("meowlearn", [
    (0, [TAG("Learn English and German by playing.")]),
    (L, [B("Short lessons, 1v1 duels with other players, a ranked leaderboard and a cat you can dress up. Built solo after hours – from design to server.")]),
])
render("conversion-toolkit", [
    (0, [TAG("Checks whether conversion tracking on a website actually works.")]),
    (L, [B("Born from my daily work – instead of a dozen separate tools after every deployment, everything is in one place:")]),
    (L, [S("24/7 monitoring"), B(" – uptime, SSL, domain expiry, code changes, GTM, GA4, Consent Mode v2 and ad pixels, with push alerts showing exactly what changed")]),
    (2, [S("Site audit"), B(" – PageSpeed, W3C, server headers and tracking in one client-ready PDF report")]),
    (2, [S("GTM builder"), B(" – a full container from ready-made templates, imported into GTM in one click")]),
    (L, [B("Free plan + Pro, Agency and Enterprise (monthly, yearly or lifetime).")]),
    (2, [B("Designed and built solo: web panel, Chrome extension, backend, monitoring and payments.")]),
])
render("chrome-extension", [
    (0, [TAG("Tracking audits right in your browser.")]),
    (L, [B("A Chrome extension for performance marketing and analytics specialists – tracking audits, Consent Mode checks and GTM setup without leaving the page.")]),
])
