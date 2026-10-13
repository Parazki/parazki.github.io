"""Eigene Produkt-Illustrationen (SVG) im Stil von Produktfotos – frei von fremden Rechten.

build.py schreibt jede Illustration nach dist/assets/bilder/<schluessel>.svg.
Jede Illustration nutzt eigene Verlaufs-IDs (Präfix = Schlüssel), damit nichts kollidiert.
"""

SCHRIFT = "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"


def _svg(key, inhalt, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="400" height="400">'
            f'<defs>{defs}<radialGradient id="{key}-sh" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0" stop-color="#000" stop-opacity=".30"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient></defs>'
            f'{inhalt}</svg>')


def _schatten(key, rx=60, cy=188):
    return f'<ellipse cx="100" cy="{cy}" rx="{rx}" ry="8" fill="url(#{key}-sh)"/>'


def _weiss(gid):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/>'
            f'<stop offset=".55" stop-color="#eef0f3"/><stop offset="1" stop-color="#cdd2d9"/></linearGradient>')


def _linear(gid, farben, x2=1, y2=1):
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in farben)
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def _radial(gid, farben, cx="50%", cy="50%", r="50%"):
    stops = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in farben)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{stops}</radialGradient>'


def kuehlschrank():
    k = "kue"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-s", [(0, "#d9dde3"), (1, "#aeb5bf")], 1, 0)
    return _svg(k, _schatten(k, 54) + f'''
<path d="M140 20 h6 a7 7 0 0 1 7 7 v150 a7 7 0 0 1 -7 7 h-6 z" fill="url(#{k}-s)"/>
<rect x="54" y="14" width="90" height="170" rx="13" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<path d="M54 72 H144" stroke="#bcc2cb" stroke-width="1.6"/>
<rect x="129" y="32" width="5.5" height="28" rx="2.7" fill="#9aa1ab"/>
<rect x="129" y="84" width="5.5" height="46" rx="2.7" fill="#9aa1ab"/>
<rect x="61" y="21" width="6" height="157" rx="3" fill="#fff" opacity=".75"/>
<rect x="70" y="80" width="26" height="9" rx="4.5" fill="#1d1d1f" opacity=".85"/>
<text x="83" y="87.3" font-family="{SCHRIFT}" font-size="7" font-weight="700" fill="#64d2ff" text-anchor="middle">4 °C</text>
<rect x="62" y="182" width="10" height="5" rx="2" fill="#8e959f"/><rect x="126" y="182" width="10" height="5" rx="2" fill="#8e959f"/>''', defs)


def fernseher():
    k = "tv"
    defs = (_linear(f"{k}-b", [(0, "#3b1fa8"), (.5, "#1563d6"), (1, "#00a6a0")])
            + f'<clipPath id="{k}-c"><rect x="19" y="35" width="162" height="102" rx="4"/></clipPath>'
            + f'<filter id="{k}-f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="13"/></filter>')
    return _svg(k, _schatten(k, 62, 184) + f'''
<path d="M91 140 h18 l7 30 h-32 z" fill="#c4c9d1"/>
<rect x="62" y="168" width="76" height="7" rx="3.5" fill="#aeb5bf"/>
<rect x="13" y="29" width="174" height="114" rx="9" fill="#1d1d1f"/>
<rect x="19" y="35" width="162" height="102" rx="4" fill="url(#{k}-b)"/>
<g clip-path="url(#{k}-c)">
  <g filter="url(#{k}-f)"><circle cx="58" cy="62" r="40" fill="#ff5fcf" opacity=".85"/><circle cx="150" cy="122" r="36" fill="#ffd60a" opacity=".75"/>
  <circle cx="128" cy="48" r="28" fill="#5ef0ff" opacity=".7"/></g>
  <path d="M19 35 L95 35 L40 137 L19 137 Z" fill="#fff" opacity=".07"/>
</g>
<circle cx="100" cy="140" r="1.4" fill="#636366"/>''', defs)


def heizluefter():
    k = "hz"
    defs = _weiss(f"{k}-k") + _radial(f"{k}-w", [(0, "#ffe08a", 1), (.55, "#ff8a1f", 1), (1, "#b83200", 1)], "50%", "60%", "70%")
    wellen = "".join(f'<path d="M{x} 46 q7 -8 0 -16 q-7 -8 0 -16" fill="none" stroke="#ff9f0a" stroke-width="3.2" stroke-linecap="round" opacity=".75"/>'
                     for x in (80, 100, 120))
    lamellen = "".join(f'<path d="M64 {y} H136" stroke="#2b2b2e" stroke-width="3.2" opacity=".55"/>' for y in range(84, 132, 8))
    return _svg(k, _schatten(k, 54) + wellen + f'''
<rect x="50" y="56" width="100" height="116" rx="24" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="63" y="72" width="74" height="64" rx="13" fill="url(#{k}-w)"/>{lamellen}
<rect x="63" y="72" width="74" height="64" rx="13" fill="none" stroke="#2b2b2e" stroke-opacity=".25"/>
<circle cx="100" cy="152" r="9" fill="#eceef1" stroke="#aab0b9" stroke-width="2"/><path d="M100 152 L100 145" stroke="#ff453a" stroke-width="2.4" stroke-linecap="round"/>
<rect x="56" y="62" width="5" height="100" rx="2.5" fill="#fff" opacity=".7"/>''', defs)


def waschmaschine():
    k = "wm"
    defs = (_weiss(f"{k}-k") + _radial(f"{k}-g", [(0, "#e6f3ff", 1), (.6, "#7fb6ee", 1), (1, "#2c5f9e", 1)], "40%", "35%", "75%")
            + f'<clipPath id="{k}-c"><circle cx="100" cy="117" r="36"/></clipPath>')
    return _svg(k, _schatten(k, 66) + f'''
<rect x="34" y="20" width="132" height="164" rx="15" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<path d="M34 52 H166" stroke="#c9ced6" stroke-width="1.6"/>
<rect x="44" y="30" width="16" height="13" rx="3" fill="#e2e5e9" stroke="#c4c9d1"/>
<rect x="72" y="29" width="44" height="15" rx="4" fill="#1d1d1f"/>
<text x="94" y="40.5" font-family="{SCHRIFT}" font-size="9.5" font-weight="700" fill="#30d158" text-anchor="middle">30°</text>
<circle cx="146" cy="36.5" r="9" fill="#eceef1" stroke="#aab0b9" stroke-width="2"/><path d="M146 36.5 L151 32" stroke="#636366" stroke-width="2" stroke-linecap="round"/>
<circle cx="100" cy="117" r="47" fill="#e3e6ea" stroke="#b7bec8" stroke-width="2"/>
<circle cx="100" cy="117" r="36" fill="url(#{k}-g)"/>
<g clip-path="url(#{k}-c)"><path d="M60 124 Q80 114 100 124 T140 124 V160 H60 Z" fill="#3d86d6" opacity=".55"/>
<circle cx="88" cy="134" r="4" fill="#fff" opacity=".5"/><circle cx="112" cy="140" r="3" fill="#fff" opacity=".45"/></g>
<path d="M76 98 A30 30 0 0 1 104 86" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7"/>
<rect x="40" y="26" width="5" height="152" rx="2.5" fill="#fff" opacity=".6"/>''', defs)


def spielkonsole():
    k = "gp"
    defs = _linear(f"{k}-k", [(0, "#4a4a4e"), (1, "#141416")])
    return _svg(k, _schatten(k, 70, 178) + f'''
<path d="M54 64 C30 64 18 86 15 116 C12 146 24 164 40 162 C54 160 60 142 72 134 H128 C140 142 146 160 160 162 C176 164 188 146 185 116 C182 86 170 64 146 64 Z" fill="url(#{k}-k)"/>
<path d="M58 70 C40 72 30 86 26 104" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".18"/>
<rect x="49" y="96" width="22" height="7" rx="2" fill="#8e8e93"/><rect x="56.5" y="88.5" width="7" height="22" rx="2" fill="#8e8e93"/>
<circle cx="142" cy="88" r="5.5" fill="#30d158"/><circle cx="154" cy="100" r="5.5" fill="#ff453a"/><circle cx="130" cy="100" r="5.5" fill="#0a84ff"/><circle cx="142" cy="112" r="5.5" fill="#ffd60a"/>
<circle cx="82" cy="124" r="11" fill="#2c2c2e" stroke="#48484a" stroke-width="2"/><circle cx="118" cy="124" r="11" fill="#2c2c2e" stroke="#48484a" stroke-width="2"/>
<rect x="88" y="84" width="24" height="5" rx="2.5" fill="#64d2ff" opacity=".9"/>''', defs)


def wasserkocher():
    k = "wk"
    defs = _linear(f"{k}-k", [(0, "#8e959f"), (.35, "#f5f5f7"), (.7, "#c9ced6"), (1, "#7d848e")], 1, 0) + _linear(f"{k}-w", [(0, "#9fd0ff"), (1, "#2f80d8")], 0, 1)
    dampf = "".join(f'<path d="M{x} 44 q-6 -7 0 -14 q6 -7 0 -14" fill="none" stroke="#a1a1a6" stroke-width="3" stroke-linecap="round" opacity=".45"/>' for x in (38, 50))
    return _svg(k, _schatten(k, 56) + dampf + f'''
<path d="M132 72 C166 72 172 122 140 140" fill="none" stroke="#2c2c2e" stroke-width="11" stroke-linecap="round"/>
<path d="M64 76 L36 62 L41 77 L62 90 Z" fill="#c9ced6" stroke="#9aa1ab"/>
<path d="M66 58 Q98 50 130 58 L142 160 Q98 168 54 160 Z" fill="url(#{k}-k)" stroke="#a5acb6"/>
<ellipse cx="98" cy="57" rx="32" ry="6" fill="#3a3a3c"/><rect x="92" y="47" width="12" height="7" rx="3" fill="#2c2c2e"/>
<rect x="74" y="88" width="10" height="56" rx="5" fill="url(#{k}-w)" stroke="#7a8590" stroke-opacity=".4"/>
<rect x="50" y="162" width="96" height="15" rx="7.5" fill="#2c2c2e"/><rect x="86" y="168" width="24" height="3" rx="1.5" fill="#0a84ff"/>''', defs)


def messgeraet():
    k = "mg"
    defs = _weiss(f"{k}-k")
    return _svg(k, _schatten(k, 46) + f'''
<rect x="92" y="14" width="5" height="18" rx="2" fill="#9aa1ab"/><rect x="103" y="14" width="5" height="18" rx="2" fill="#9aa1ab"/>
<rect x="50" y="28" width="100" height="148" rx="24" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="64" y="44" width="72" height="38" rx="8" fill="#1d1d1f"/>
<text x="100" y="70" font-family="{SCHRIFT}" font-size="19" font-weight="700" fill="#30d158" text-anchor="middle">42 W</text>
<rect x="76" y="88" width="20" height="6" rx="3" fill="#d5d9df"/><rect x="104" y="88" width="20" height="6" rx="3" fill="#d5d9df"/>
<circle cx="100" cy="134" r="29" fill="#eef0f3" stroke="#c4c9d1" stroke-width="2"/>
<circle cx="88" cy="134" r="4.5" fill="#7d848e"/><circle cx="112" cy="134" r="4.5" fill="#7d848e"/>
<rect x="96" y="106" width="8" height="5" rx="1.5" fill="#b5bbc4"/><rect x="96" y="157" width="8" height="5" rx="1.5" fill="#b5bbc4"/>
<rect x="56" y="34" width="5" height="136" rx="2.5" fill="#fff" opacity=".7"/>''', defs)


def balkonkraftwerk():
    k = "bk"
    defs = _linear(f"{k}-c", [(0, "#2a63bd"), (1, "#0d2a5c")]) + _radial(f"{k}-sonne", [(0, "#ffd60a", .55), (1, "#ffd60a", 0)])
    linien = []
    for i in range(1, 6):
        xt = 73 + i * (172 - 73) / 6
        xb = 36 + i * (145 - 36) / 6
        linien.append(f'<path d="M{xt:.1f} 67 L{xb:.1f} 145" stroke="#7fa6e0" stroke-width="1" opacity=".6"/>')
    for j in range(1, 4):
        y = 67 + j * (145 - 67) / 4
        xl = 73 - (73 - 36) * j / 4
        xr = 172 - (172 - 145) * j / 4
        linien.append(f'<path d="M{xl:.1f} {y:.1f} L{xr:.1f} {y:.1f}" stroke="#7fa6e0" stroke-width="1" opacity=".6"/>')
    return _svg(k, f'''<circle cx="160" cy="38" r="34" fill="url(#{k}-sonne)"/><circle cx="160" cy="38" r="16" fill="#ffd60a"/>''' + _schatten(k, 68, 184) + f'''
<path d="M62 150 L66 178" stroke="#9aa1ab" stroke-width="4.5" stroke-linecap="round"/><path d="M138 150 L134 178" stroke="#9aa1ab" stroke-width="4.5" stroke-linecap="round"/>
<polygon points="30,151 70,61 179,61 151,151" fill="#d5d9df" stroke="#aeb5bf"/>
<polygon points="36,145 73,67 172,67 145,145" fill="url(#{k}-c)"/>{"".join(linien)}
<polygon points="73,67 120,67 70,145 36,145" fill="#fff" opacity=".10"/>
<rect x="88" y="160" width="26" height="16" rx="4" fill="#2c2c2e"/><circle cx="108" cy="168" r="2" fill="#30d158"/>''', defs)


def heizdecke():
    k = "hd"
    defs = (_linear(f"{k}-o", [(0, "#ffc9aa"), (1, "#f2875a")], 0, 1)
            + _linear(f"{k}-v", [(0, "#e2643c"), (1, "#a93c25")], 0, 1)
            + f'<clipPath id="{k}-c"><path d="M46 84 H154 Q162 84 165 92 L178 136 Q180 144 172 144 H28 Q20 144 22 136 L35 92 Q38 84 46 84 Z"/></clipPath>')
    stiche = "".join(f'<path d="M{x} 84 L{x + 60} 144 M{x + 60} 84 L{x} 144" stroke="#fff" stroke-width="1.4" stroke-dasharray="3 3" opacity=".45"/>'
                     for x in range(-40, 200, 22))
    waerme = "".join(f'<path d="M{x} 70 q6 -7 0 -14 q-6 -7 0 -14" fill="none" stroke="#ff9f0a" stroke-width="3" stroke-linecap="round" opacity=".7"/>'
                     for x in (72, 100, 128))
    return _svg(k, _schatten(k, 74) + waerme + f'''
<rect x="21" y="128" width="158" height="40" rx="12" fill="url(#{k}-v)"/>
<path d="M28 156 H172" stroke="#fff" stroke-width="1.5" opacity=".18"/>
<path d="M46 84 H154 Q162 84 165 92 L178 136 Q180 144 172 144 H28 Q20 144 22 136 L35 92 Q38 84 46 84 Z" fill="url(#{k}-o)"/>
<g clip-path="url(#{k}-c)">{stiche}</g>
<path d="M44 90 H150" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".55"/>
<path d="M176 150 C194 152 194 170 182 174" fill="none" stroke="#c4c9d1" stroke-width="3"/>
<rect x="164" y="166" width="24" height="30" rx="8" fill="#f5f5f7" stroke="#c4c9d1"/>
<circle cx="176" cy="177" r="4" fill="#ff9f0a"/><circle cx="170" cy="188" r="1.6" fill="#ff9f0a"/><circle cx="176" cy="188" r="1.6" fill="#ff9f0a"/><circle cx="182" cy="188" r="1.6" fill="#c4c9d1"/>''', defs)


def sparduschkopf():
    k = "du"
    defs = _linear(f"{k}-c", [(0, "#ffffff"), (.5, "#c3c8cf"), (1, "#8f969f")], 0, 1)
    duesen = "".join(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#8f969f"/>' for x in range(72, 132, 8) for y in (82, 88) if abs(x - 100) < 34 - (y - 82) * 2)
    strahlen = "".join(
        f'<path d="M{x} 98 L{x - (x - 100) * .3:.1f} 176" stroke="#4aa3ff" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="7 9" opacity=".75"/>'
        for x in range(72, 132, 8))
    return _svg(k, _schatten(k, 46) + strahlen + f'''
<path d="M176 26 H122 Q100 26 100 48 V64" fill="none" stroke="#b5bbc4" stroke-width="11" stroke-linecap="round"/>
<ellipse cx="100" cy="78" rx="45" ry="15" fill="url(#{k}-c)" stroke="#9aa1ab"/>
<ellipse cx="100" cy="85" rx="41" ry="10" fill="#e3e6ea"/>{duesen}
<circle cx="154" cy="138" r="17" fill="#30d158"/>
<path d="M146 144 C146 132 156 128 163 130 C163 140 156 146 146 144 Z M146 144 L157 134" fill="#fff" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/>''', defs)


def steckdosenleiste(master=False):
    k = "ms" if master else "sl"
    defs = _weiss(f"{k}-k")
    dosen = []
    for i, x in enumerate((38, 72, 106, 140)):
        rand = "#30d158" if master and i == 0 else "#c4c9d1"
        dosen.append(f'<circle cx="{x}" cy="104" r="14.5" fill="#eef0f3" stroke="{rand}" stroke-width="{3 if master and i == 0 else 1.5}"/>'
                     f'<circle cx="{x - 5.5}" cy="104" r="2.6" fill="#7d848e"/><circle cx="{x + 5.5}" cy="104" r="2.6" fill="#7d848e"/>')
    schalter = "#30d158" if master else "#ff453a"
    marke = f'<text x="38" y="132" font-family="{SCHRIFT}" font-size="8" font-weight="700" fill="#30d158" text-anchor="middle">MASTER</text>' if master else ""
    return _svg(k, _schatten(k, 78, 150) + f'''
<path d="M14 104 C-4 104 2 150 34 160 C64 170 76 178 98 180" fill="none" stroke="#c4c9d1" stroke-width="5" stroke-linecap="round"/>
<rect x="14" y="80" width="176" height="48" rx="15" fill="url(#{k}-k)" stroke="#c4c9d1"/>{"".join(dosen)}{marke}
<rect x="160" y="91" width="22" height="26" rx="6" fill="{schalter}"/><rect x="163" y="94" width="16" height="9" rx="3" fill="#fff" opacity=".35"/>
<rect x="20" y="84" width="150" height="4" rx="2" fill="#fff" opacity=".7"/>''', defs)


def waeschestaender():
    k = "ws"
    tuecher = (
        '<rect x="48" y="66" width="34" height="62" rx="4" fill="#4aa3ff"/><rect x="48" y="112" width="34" height="5" fill="#fff" opacity=".6"/>'
        '<rect x="90" y="66" width="30" height="48" rx="4" fill="#ff9f0a"/><rect x="90" y="100" width="30" height="4" fill="#fff" opacity=".55"/>'
        '<rect x="128" y="66" width="28" height="56" rx="4" fill="#30d158"/><rect x="128" y="108" width="28" height="4" fill="#fff" opacity=".55"/>')
    return _svg(k, _schatten(k, 70, 184) + f'''
<path d="M38 182 L162 70 M162 182 L38 70" stroke="#aeb5bf" stroke-width="5" stroke-linecap="round"/>
<path d="M30 64 H170" stroke="#c4c9d1" stroke-width="5" stroke-linecap="round"/>
<path d="M36 58 H164 M42 52 H158" stroke="#d5d9df" stroke-width="3" stroke-linecap="round"/>{tuecher}''')


def zeitschaltuhr():
    k = "zs"
    import math
    segmente = []
    for i in range(24):
        a = math.radians(i * 15 - 90)
        x1, y1 = 100 + 26 * math.cos(a), 84 + 26 * math.sin(a)
        x2, y2 = 100 + 34 * math.cos(a), 84 + 34 * math.sin(a)
        farbe = "#ff9f0a" if 7 <= i <= 14 else "#c4c9d1"
        segmente.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{farbe}" stroke-width="4" stroke-linecap="round"/>')
    return _svg(k, _schatten(k, 50) + f'''
<rect x="50" y="30" width="100" height="148" rx="24" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<circle cx="100" cy="84" r="40" fill="#f3f4f6" stroke="#c4c9d1" stroke-width="2"/>{"".join(segmente)}
<circle cx="100" cy="84" r="14" fill="#fff" stroke="#aab0b9" stroke-width="2"/><path d="M100 84 L100 74" stroke="#1d1d1f" stroke-width="2.4" stroke-linecap="round"/>
<path d="M95 40 L105 40 L100 47 Z" fill="#1d1d1f"/>
<circle cx="100" cy="148" r="17" fill="#eef0f3" stroke="#c4c9d1" stroke-width="1.5"/><circle cx="94" cy="148" r="3" fill="#7d848e"/><circle cx="106" cy="148" r="3" fill="#7d848e"/>
<rect x="56" y="36" width="5" height="136" rx="2.5" fill="#fff" opacity=".7"/>''', _weiss(f"{k}-k"))


def led():
    k = "led"
    defs = (_radial(f"{k}-g", [(0, "#fffdf0", 1), (.55, "#ffe9a8", 1), (1, "#ffc94a", 1)], "45%", "40%", "65%")
            + _radial(f"{k}-gl", [(0, "#ffd60a", .55), (1, "#ffd60a", 0)]))
    return _svg(k, f'<circle cx="100" cy="78" r="80" fill="url(#{k}-gl)"/>' + _schatten(k, 34, 190) + f'''
<path d="M100 20 C63 20 43 49 45 79 C47 103 63 116 70 130 L130 130 C137 116 153 103 155 79 C157 49 137 20 100 20 Z" fill="url(#{k}-g)" stroke="#f2c14e" stroke-opacity=".6"/>
<path d="M90 128 L93 66 M100 128 L100 60 M110 128 L107 66" stroke="#ff9f0a" stroke-width="2.6" stroke-linecap="round" opacity=".85"/>
<path d="M70 52 C76 38 88 32 98 31" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".8"/>
<rect x="70" y="130" width="60" height="11" rx="3" fill="#d5d9df"/>
<rect x="72" y="143" width="56" height="8" rx="4" fill="#b5bbc4"/><rect x="74" y="153" width="52" height="8" rx="4" fill="#a5acb6"/><rect x="78" y="163" width="44" height="8" rx="4" fill="#959ca6"/>
<circle cx="100" cy="178" r="6" fill="#636366"/>''', defs)


def thermometer():
    k = "th"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-s", [(0, "#64d2ff"), (.5, "#30d158"), (1, "#ff453a")], 1, 0)
    return _svg(k, _schatten(k, 42) + f'''
<path d="M100 14 C88 14 88 34 100 34" fill="none" stroke="#aeb5bf" stroke-width="4" stroke-linecap="round"/>
<rect x="60" y="34" width="80" height="136" rx="22" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="71" y="52" width="58" height="50" rx="9" fill="#1d1d1f"/>
<text x="100" y="86" font-family="{SCHRIFT}" font-size="27" font-weight="700" fill="#64d2ff" text-anchor="middle">7°</text>
<rect x="76" y="116" width="48" height="7" rx="3.5" fill="url(#{k}-s)"/><circle cx="92" cy="119.5" r="5" fill="#fff" stroke="#1d1d1f" stroke-width="2"/>
<circle cx="100" cy="146" r="8" fill="#eceef1" stroke="#aab0b9" stroke-width="2"/>
<rect x="66" y="40" width="5" height="124" rx="2.5" fill="#fff" opacity=".7"/>''', defs)


# ---------------------------------------------------------------- Bausteine für die Geräte-Bilder

def _dunkel(gid):
    return _linear(gid, [(0, "#4a4a4e"), (1, "#141416")])


def _metall(gid):
    return _linear(gid, [(0, "#9aa1ab"), (.3, "#f5f5f7"), (.65, "#cdd2d9"), (1, "#8e959f")], 1, 0)


def _glanz(x, y, h):
    return f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2.5" fill="#fff" opacity=".7"/>'


def _anzeige(x, y, w, h, text, farbe="#30d158", groesse=10):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{min(h / 3, 8):.1f}" fill="#1d1d1f"/>'
            f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + groesse * .36:.1f}" font-family="{SCHRIFT}" font-size="{groesse}" '
            f'font-weight="700" fill="{farbe}" text-anchor="middle">{text}</text>')


def _knopf(cx, cy, r=8, zeiger="#636366"):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#eceef1" stroke="#aab0b9" stroke-width="2"/>'
            f'<path d="M{cx} {cy} L{cx} {cy - r + 2.5}" stroke="{zeiger}" stroke-width="2.2" stroke-linecap="round"/>')


def _wellen(xs, y, farbe="#ff9f0a", hoehe=7):
    return "".join(f'<path d="M{x} {y} q{hoehe * .85:.1f} -{hoehe} 0 -{hoehe * 2} q-{hoehe * .85:.1f} -{hoehe} 0 -{hoehe * 2}" fill="none" '
                   f'stroke="{farbe}" stroke-width="3" stroke-linecap="round" opacity=".65"/>' for x in xs)


def _blitz(cx, cy, s=1.0, farbe="#ffd60a"):
    return (f'<path transform="translate({cx} {cy}) scale({s})" d="M3 -14 L-8 2 H-1 L-4 14 L8 -3 H1 Z" fill="{farbe}" '
            f'stroke="{farbe}" stroke-width="1.5" stroke-linejoin="round"/>')


def _bogen(cx, cy, radien, farbe, breite=4):
    teile = []
    for i, r in enumerate(radien):
        d = r * .7071
        teile.append(f'<path d="M{cx - d:.1f} {cy - d:.1f} A{r} {r} 0 0 1 {cx + d:.1f} {cy - d:.1f}" fill="none" stroke="{farbe}" '
                     f'stroke-width="{breite}" stroke-linecap="round" opacity="{1 - i * .25:.2f}"/>')
    return "".join(teile)


# ---------------------------------------------------------------- Küche und Haushalt

def gefrierschrank():
    k = "gf"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-s", [(0, "#d9dde3"), (1, "#aeb5bf")], 1, 0)
    return _svg(k, _schatten(k, 54) + f'''
<path d="M140 20 h6 a7 7 0 0 1 7 7 v150 a7 7 0 0 1 -7 7 h-6 z" fill="url(#{k}-s)"/>
<rect x="54" y="14" width="90" height="170" rx="13" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="129" y="30" width="5.5" height="64" rx="2.7" fill="#9aa1ab"/>
{_anzeige(72, 32, 44, 18, "−18°", "#64d2ff", 11)}
<g stroke="#64d2ff" stroke-width="3" stroke-linecap="round"><path d="M94 70 V108 M77.5 79.5 L110.5 98.5 M77.5 98.5 L110.5 79.5"/>
<path d="M88 72 L94 77 L100 72 M88 106 L94 101 L100 106" fill="none" stroke-width="2.2"/></g>
<path d="M54 160 H144" stroke="#c9ced6" stroke-width="1.4"/>
{_glanz(61, 21, 157)}
<rect x="62" y="182" width="10" height="5" rx="2" fill="#8e959f"/><rect x="126" y="182" width="10" height="5" rx="2" fill="#8e959f"/>''', defs)


def trockner(wp=True):
    k = "twp" if wp else "tko"
    defs = (_weiss(f"{k}-k") + _radial(f"{k}-g", [(0, "#7a828d", 1), (.7, "#3a3f47", 1), (1, "#1f2329", 1)], "40%", "35%", "75%")
            + f'<clipPath id="{k}-c"><circle cx="100" cy="117" r="36"/></clipPath>')
    if wp:
        marke = ('<circle cx="146" cy="166" r="10" fill="#30d158"/>'
                 '<path d="M140 171 C140 160 149 156 153 158 C153 167 147 172 140 171 Z M140 171 L149 162" fill="#fff" stroke="#fff" stroke-width="1.3" stroke-linejoin="round"/>')
    else:
        marke = '<circle cx="146" cy="166" r="10" fill="#ff9f0a"/>' + _wellen((142, 150), 174, "#fff", 4)
    return _svg(k, _schatten(k, 66) + f'''
<rect x="34" y="20" width="132" height="164" rx="15" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<path d="M34 52 H166" stroke="#c9ced6" stroke-width="1.6"/>
<rect x="44" y="30" width="16" height="13" rx="3" fill="#e2e5e9" stroke="#c4c9d1"/>
{_anzeige(72, 29, 44, 15, "Eco" if wp else "2:10", "#30d158" if wp else "#ff9f0a", 9.5)}
{_knopf(146, 36.5, 9)}
<circle cx="100" cy="117" r="47" fill="#e3e6ea" stroke="#b7bec8" stroke-width="2"/>
<circle cx="100" cy="117" r="36" fill="url(#{k}-g)"/>
<g clip-path="url(#{k}-c)"><circle cx="86" cy="132" r="15" fill="#ff9f0a" opacity=".85"/><circle cx="114" cy="138" r="17" fill="#0a84ff" opacity=".8"/>
<circle cx="102" cy="116" r="11" fill="#ff375f" opacity=".75"/></g>
<path d="M76 98 A30 30 0 0 1 104 86" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".55"/>
{marke}{_glanz(40, 26, 152)}''', defs)


def geschirrspueler():
    k = "gs"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-i", [(0, "#4a5059"), (1, "#22262c")], 0, 1)
    teller = "".join(f'<ellipse cx="{x}" cy="94" rx="4.6" ry="21" fill="#f7f9fc" stroke="#c4c9d1"/>' for x in range(62, 142, 11))
    return _svg(k, _schatten(k, 72) + f'''
<rect x="40" y="30" width="120" height="98" rx="10" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="40" y="30" width="120" height="14" rx="7" fill="#e3e6ea"/>
{_anzeige(50, 33, 30, 9, "Eco", "#30d158", 6.5)}
<circle cx="134" cy="37.5" r="2.4" fill="#aeb5bf"/><circle cx="144" cy="37.5" r="2.4" fill="#aeb5bf"/><circle cx="124" cy="37.5" r="2.4" fill="#30d158"/>
<rect x="50" y="50" width="100" height="74" rx="4" fill="url(#{k}-i)"/>
{teller}
<path d="M54 116 H146 M54 116 V108 M146 116 V108" stroke="#aeb5bf" stroke-width="2" fill="none"/>
<polygon points="40,128 160,128 178,176 22,176" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<polygon points="54,134 146,134 158,168 42,168" fill="#dfe3e8"/>
<rect x="88" y="142" width="24" height="12" rx="3" fill="#c9ced6"/>
<path d="M60 162 H140" stroke="#c4c9d1" stroke-width="2" stroke-dasharray="3 5"/>''', defs)


def kaffeevollautomat():
    k = "kv"
    defs = _dunkel(f"{k}-k") + _metall(f"{k}-m") + _linear(f"{k}-d", [(0, "#1c2a3a"), (1, "#0b1018")], 0, 1)
    return _svg(k, _schatten(k, 56) + f'''
<rect x="52" y="22" width="96" height="156" rx="16" fill="url(#{k}-k)"/>
<ellipse cx="100" cy="24" rx="34" ry="5" fill="#2c2c2e"/>
<rect x="64" y="36" width="72" height="32" rx="6" fill="url(#{k}-d)" stroke="#3a3a3c"/>
<circle cx="80" cy="52" r="6" fill="#c08a4f"/><circle cx="100" cy="52" r="6" fill="#f5f5f7"/><circle cx="120" cy="52" r="6" fill="#8e5a2e"/>
<rect x="64" y="78" width="72" height="80" rx="9" fill="#0d0d0f"/>
<rect x="86" y="78" width="28" height="13" rx="3" fill="url(#{k}-m)"/>
<rect x="91" y="91" width="5" height="5" rx="1" fill="#8e959f"/><rect x="104" y="91" width="5" height="5" rx="1" fill="#8e959f"/>
<path d="M93.5 97 V124 M106.5 97 V124" stroke="#7a4a22" stroke-width="2" stroke-linecap="round" opacity=".9"/>
<path d="M82 124 H118 V144 Q118 150 112 150 H88 Q82 150 82 144 Z" fill="#fff"/>
<path d="M118 129 Q127 129 127 136 Q127 143 118 143" fill="none" stroke="#fff" stroke-width="3.5"/>
<ellipse cx="100" cy="125" rx="17" ry="3" fill="#c08a4f"/>
<rect x="62" y="152" width="76" height="9" rx="3" fill="url(#{k}-m)"/>
<path d="M58 30 V168" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".14"/>''', defs)


def backofen():
    k = "bo"
    defs = (_metall(f"{k}-m") + _radial(f"{k}-g", [(0, "#ffd27a", 1), (.6, "#ff8a1f", 1), (1, "#5a1e00", 1)], "50%", "45%", "70%"))
    return _svg(k, _schatten(k, 72) + f'''
<rect x="26" y="24" width="148" height="154" rx="10" fill="url(#{k}-m)" stroke="#9aa1ab"/>
<rect x="30" y="28" width="140" height="24" rx="7" fill="#1d1d1f"/>
<text x="100" y="45" font-family="{SCHRIFT}" font-size="12" font-weight="700" fill="#ff9f0a" text-anchor="middle">180°</text>
<circle cx="46" cy="40" r="7" fill="url(#{k}-m)"/><circle cx="154" cy="40" r="7" fill="url(#{k}-m)"/>
<rect x="34" y="58" width="132" height="114" rx="6" fill="#2a2d33"/>
<rect x="44" y="64" width="112" height="7" rx="3.5" fill="url(#{k}-m)"/>
<rect x="46" y="80" width="108" height="82" rx="6" fill="url(#{k}-g)"/>
<path d="M50 140 H150" stroke="#3a1400" stroke-width="2" opacity=".6"/>
<path d="M66 138 Q66 118 100 116 Q134 118 134 138 Z" fill="#9a4f1c"/><path d="M74 128 Q100 120 126 128" fill="none" stroke="#d98a4a" stroke-width="2.5" stroke-linecap="round"/>
<polygon points="46,80 92,80 58,162 46,162" fill="#fff" opacity=".08"/>''', defs)


def elektroherd():
    k = "eh"
    defs = (_linear(f"{k}-g", [(0, "#3a3a3c"), (1, "#0d0d0f")], 0, 1)
            + _radial(f"{k}-r", [(0, "#ffb340", 1), (.45, "#ff453a", 1), (1, "#7a0d06", 1)]))
    return _svg(k, _wellen((70, 82), 104, "#ff9f0a", 6) + _wellen((126,), 76, "#ff9f0a", 5) + _schatten(k, 82, 176) + f'''
<polygon points="20,150 50,74 150,74 180,150" fill="url(#{k}-g)" stroke="#48484a" stroke-linejoin="round"/>
<polygon points="20,150 180,150 180,159 20,159" fill="#8e959f"/>
<ellipse cx="76" cy="92" rx="22" ry="8.5" fill="none" stroke="#636366" stroke-width="2"/>
<ellipse cx="126" cy="92" rx="17" ry="7" fill="url(#{k}-r)" opacity=".95"/><ellipse cx="126" cy="92" rx="11" ry="4.5" fill="none" stroke="#ffcf7a" stroke-width="1.2" opacity=".7"/>
<ellipse cx="70" cy="126" rx="29" ry="12" fill="url(#{k}-r)"/><ellipse cx="70" cy="126" rx="19" ry="7.8" fill="none" stroke="#ffcf7a" stroke-width="1.4" opacity=".7"/>
<ellipse cx="70" cy="126" rx="9" ry="3.6" fill="none" stroke="#ffcf7a" stroke-width="1.2" opacity=".6"/>
<ellipse cx="134" cy="126" rx="24" ry="10" fill="none" stroke="#636366" stroke-width="2"/>
<circle cx="88" cy="143" r="2.6" fill="#ff453a"/><circle cx="98" cy="143" r="2.6" fill="#636366"/><circle cx="108" cy="143" r="2.6" fill="#636366"/><circle cx="118" cy="143" r="2.6" fill="#636366"/>
<polygon points="50,74 96,74 64,150 20,150" fill="#fff" opacity=".05"/>''', defs)


def heissluftfritteuse():
    k = "hl"
    defs = _dunkel(f"{k}-k")
    schlitze = "".join(f'<rect x="{x}" y="72" width="3" height="12" rx="1.5" fill="#0d0d0f"/>' for x in range(76, 126, 8))
    return _svg(k, _wellen((86, 114), 26, "#ff9f0a", 5) + _schatten(k, 52) + f'''
<path d="M54 64 Q54 32 100 32 Q146 32 146 64 V164 Q146 178 132 178 H68 Q54 178 54 164 Z" fill="url(#{k}-k)"/>
{_anzeige(76, 42, 48, 20, "200°", "#ff9f0a", 11)}
{schlitze}
<rect x="62" y="96" width="76" height="74" rx="11" fill="#2c2c2e" stroke="#48484a"/>
<rect x="84" y="114" width="32" height="38" rx="7" fill="#48484a" stroke="#636366"/>
<path d="M60 44 Q58 100 60 160" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".15"/>''', defs)


def mikrowelle():
    k = "mw"
    defs = (_linear(f"{k}-k", [(0, "#f5f5f7"), (1, "#bfc5cd")])
            + _radial(f"{k}-l", [(0, "#ffe9a8", 1), (.6, "#e0a540", 1), (1, "#5a3a00", 1)], "45%", "55%", "70%"))
    return _svg(k, _schatten(k, 80, 176) + f'''
<rect x="20" y="56" width="160" height="108" rx="12" fill="url(#{k}-k)" stroke="#aeb5bf"/>
<rect x="30" y="66" width="106" height="88" rx="6" fill="#1d1d1f"/>
<rect x="36" y="72" width="94" height="76" rx="4" fill="url(#{k}-l)" opacity=".92"/>
<ellipse cx="83" cy="136" rx="34" ry="6" fill="#fff" opacity=".35"/>
<path d="M66 122 H100 Q100 136 83 136 Q66 136 66 122 Z" fill="#f5f5f7"/><ellipse cx="83" cy="122" rx="17" ry="3" fill="#ff9f0a"/>
<polygon points="36,72 74,72 46,148 36,148" fill="#fff" opacity=".1"/>
{_anzeige(144, 70, 28, 14, "0:45", "#30d158", 7.5)}
{_knopf(158, 108, 10)}
<rect x="146" y="132" width="24" height="10" rx="5" fill="#d5d9df" stroke="#aeb5bf"/>
<rect x="32" y="164" width="12" height="5" rx="2" fill="#8e959f"/><rect x="156" y="164" width="12" height="5" rx="2" fill="#8e959f"/>''', defs)


def weinkuehlschrank():
    k = "wkue"
    defs = (_linear(f"{k}-k", [(0, "#3a3a3c"), (1, "#111113")])
            + _radial(f"{k}-g", [(0, "#2d6db8", 1), (1, "#081624", 1)], "50%", "40%", "80%"))
    reihen = []
    for y in (58, 90, 122, 154):
        reihen.append(f'<rect x="68" y="{y}" width="64" height="3" fill="#8a5530"/>')
        reihen.append("".join(f'<circle cx="{x}" cy="{y - 7}" r="5.6" fill="#5a0f1e" stroke="#9a2a40" stroke-width="1.2"/>'
                              f'<circle cx="{x - 1.6}" cy="{y - 8.6}" r="1.4" fill="#fff" opacity=".45"/>' for x in (76, 88, 100, 112, 124)))
    return _svg(k, _schatten(k, 48) + f'''
<rect x="60" y="16" width="80" height="168" rx="10" fill="url(#{k}-k)"/>
<rect x="66" y="22" width="68" height="152" rx="6" fill="url(#{k}-g)" stroke="#48484a"/>
{"".join(reihen)}
{_anzeige(84, 27, 32, 12, "12°", "#64d2ff", 8)}
<rect x="128" y="52" width="4" height="84" rx="2" fill="#aeb5bf"/>
<polygon points="66,22 98,22 74,174 66,174" fill="#fff" opacity=".07"/>''', defs)


def toaster():
    k = "to"
    defs = _metall(f"{k}-m") + _linear(f"{k}-t", [(0, "#f6cf8c"), (1, "#c7853a")], 0, 1)
    return _svg(k, _schatten(k, 64, 180) + f'''
<rect x="62" y="36" width="30" height="48" rx="8" fill="url(#{k}-t)" stroke="#a8642a" stroke-width="2.5"/>
<rect x="108" y="44" width="30" height="40" rx="8" fill="url(#{k}-t)" stroke="#a8642a" stroke-width="2.5"/>
<path d="M44 96 Q44 70 68 70 H132 Q156 70 156 96 V160 Q156 174 142 174 H58 Q44 174 44 160 Z" fill="url(#{k}-m)" stroke="#9aa1ab"/>
<rect x="60" y="68" width="34" height="6" rx="3" fill="#1d1d1f"/><rect x="106" y="68" width="34" height="6" rx="3" fill="#1d1d1f"/>
<rect x="156" y="104" width="12" height="9" rx="3" fill="#2c2c2e"/>
{_knopf(100, 138, 10)}
<path d="M52 86 Q50 120 52 156" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".6"/>''', defs)


def dunstabzugshaube():
    k = "dh"
    defs = _metall(f"{k}-m") + _linear(f"{k}-l", [(0, "#fff3c4"), (1, "#fff3c4")], 0, 1)
    return _svg(k, f'''
<polygon points="56,142 72,142 88,196 38,196" fill="#ffe9a8" opacity=".35"/><polygon points="128,142 144,142 162,196 112,196" fill="#ffe9a8" opacity=".35"/>
<path d="M90 184 q-6 -8 0 -16 q6 -8 0 -16 M110 186 q-6 -8 0 -16 q6 -8 0 -16" fill="none" stroke="#a1a1a6" stroke-width="3" stroke-linecap="round" opacity=".4"/>
<rect x="80" y="12" width="40" height="76" fill="url(#{k}-m)" stroke="#9aa1ab"/>
<polygon points="34,124 80,84 120,84 166,124" fill="url(#{k}-m)" stroke="#9aa1ab" stroke-linejoin="round"/>
<rect x="30" y="124" width="140" height="18" rx="3" fill="#d5d9df" stroke="#9aa1ab"/>
<circle cx="64" cy="142" r="4" fill="#fff8d6"/><circle cx="136" cy="142" r="4" fill="#fff8d6"/>
<rect x="88" y="130" width="6" height="6" rx="1.5" fill="#636366"/><rect x="97" y="130" width="6" height="6" rx="1.5" fill="#30d158"/><rect x="106" y="130" width="6" height="6" rx="1.5" fill="#636366"/>''', defs)


def elektrogrill():
    k = "eg"
    defs = _linear(f"{k}-p", [(0, "#3a3a3c"), (1, "#141416")], 0, 1) + _radial(f"{k}-h", [(0, "#ff7a1f", .55), (1, "#ff7a1f", 0)])
    rillen = []
    for i in range(1, 8):
        t = i / 8
        xl, xr = 24 + (56 - 24) * (1 - t), 176 - (176 - 144) * (1 - t)
        y = 86 + (120 - 86) * t
        rillen.append(f'<path d="M{xl:.1f} {y:.1f} H{xr:.1f}" stroke="#55555a" stroke-width="2.4"/>')
    return _svg(k, f'''<path d="M84 64 q-6 -8 0 -16 q6 -8 0 -16 M112 60 q-6 -8 0 -16 q6 -8 0 -16" fill="none" stroke="#a1a1a6" stroke-width="3" stroke-linecap="round" opacity=".4"/>'''
                + _schatten(k, 80, 182) + f'''
<rect x="38" y="138" width="8" height="38" rx="3" fill="#2c2c2e"/><rect x="154" y="138" width="8" height="38" rx="3" fill="#2c2c2e"/>
<polygon points="24,120 56,86 144,86 176,120" fill="url(#{k}-p)"/>{"".join(rillen)}
<ellipse cx="100" cy="104" rx="70" ry="18" fill="url(#{k}-h)"/>
<g transform="rotate(-8 92 100)"><rect x="70" y="94" width="46" height="12" rx="6" fill="#c8643c"/><path d="M80 96 l4 8 M92 96 l4 8 M104 96 l4 8" stroke="#6e2a12" stroke-width="2" stroke-linecap="round"/></g>
<g transform="rotate(4 120 110)"><rect x="98" y="104" width="46" height="12" rx="6" fill="#d0703f"/><path d="M108 106 l4 8 M120 106 l4 8 M132 106 l4 8" stroke="#6e2a12" stroke-width="2" stroke-linecap="round"/></g>
<rect x="24" y="120" width="152" height="20" rx="6" fill="#1d1d1f"/>
<circle cx="40" cy="130" r="3" fill="#ff453a"/>{_knopf(160, 130, 6.5)}''', defs)


def buegeleisen():
    k = "be"
    defs = _metall(f"{k}-m") + _linear(f"{k}-b", [(0, "#64d2ff"), (1, "#0a6fd6")], 0, 1)
    return _svg(k, f'''<circle cx="30" cy="168" r="9" fill="#d1d1d6" opacity=".7"/><circle cx="44" cy="178" r="7" fill="#d1d1d6" opacity=".6"/>
<circle cx="18" cy="180" r="6" fill="#d1d1d6" opacity=".5"/>''' + _schatten(k, 70, 176) + f'''
<path d="M166 110 C186 116 188 140 180 160" fill="none" stroke="#c4c9d1" stroke-width="4" stroke-linecap="round"/>
<path d="M28 152 Q36 128 72 124 H160 Q170 124 170 134 V152 Z" fill="url(#{k}-m)" stroke="#9aa1ab"/>
<path d="M36 128 Q52 92 106 88 H150 Q166 88 166 104 V126 H40 Z" fill="url(#{k}-b)"/>
<path d="M92 90 Q96 60 124 60 H148 Q160 60 158 78 V92" fill="none" stroke="#0a6fd6" stroke-width="11" stroke-linecap="round"/>
<path d="M104 64 H146" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".35"/>
<ellipse cx="72" cy="112" rx="15" ry="8" fill="#d7ecff" opacity=".75"/>
<circle cx="132" cy="108" r="7" fill="#fff"/><path d="M132 108 L132 103" stroke="#0a6fd6" stroke-width="2" stroke-linecap="round"/>''', defs)


def staubsauger():
    k = "ss"
    defs = _linear(f"{k}-b", [(0, "#bf5af2"), (1, "#5e5ce6")], 0, 1)
    return _svg(k, _schatten(k, 52, 182) + f'''
<path d="M124 60 L84 162" stroke="#aeb5bf" stroke-width="7" stroke-linecap="round"/>
<path d="M124 60 L84 162" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".5"/>
<g transform="rotate(22 124 60)">
  <rect x="118" y="8" width="12" height="24" rx="5" fill="#2c2c2e"/>
  <rect x="110" y="28" width="28" height="62" rx="12" fill="url(#{k}-b)"/>
  <rect x="114" y="56" width="20" height="30" rx="8" fill="#e8f0ff" opacity=".75"/>
  <rect x="116" y="34" width="16" height="4" rx="2" fill="#fff" opacity=".6"/>
</g>
<path d="M54 162 H118 Q128 162 128 170 V174 Q128 180 122 180 H50 Q44 180 44 174 V170 Q44 162 54 162 Z" fill="#2c2c2e"/>
<rect x="50" y="174" width="72" height="3" rx="1.5" fill="#64d2ff"/>''', defs)


def saugroboter():
    k = "sr"
    defs = _linear(f"{k}-k", [(0, "#4a4a4e"), (1, "#111113")], 0, 1)
    return _svg(k, _schatten(k, 78, 160) + f'''
<ellipse cx="100" cy="132" rx="74" ry="30" fill="#0d0d0f"/>
<ellipse cx="100" cy="122" rx="74" ry="30" fill="url(#{k}-k)"/>
<ellipse cx="100" cy="122" rx="60" ry="23" fill="none" stroke="#55555a" stroke-width="1.5"/>
<ellipse cx="100" cy="108" rx="17" ry="7" fill="#1d1d1f"/><ellipse cx="100" cy="104" rx="17" ry="7" fill="#3a3a3c"/>
<path d="M66 110 Q100 96 134 110" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".14"/>
<rect x="92" y="136" width="16" height="3" rx="1.5" fill="#30d158"/>
<path d="M40 146 L24 150 M40 146 L30 160 M40 146 L44 162" stroke="#8e959f" stroke-width="2" stroke-linecap="round"/>''', defs)


def untertischboiler():
    k = "ub"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-t", [(0, "#0a84ff"), (1, "#ff453a")], 1, 0)
    return _svg(k, _schatten(k, 50, 172) + f'''
<path d="M84 46 V14" stroke="#0a84ff" stroke-width="7" stroke-linecap="round"/><path d="M116 46 V14" stroke="#ff453a" stroke-width="7" stroke-linecap="round"/>
<rect x="56" y="40" width="88" height="124" rx="16" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<text x="100" y="62" font-family="{SCHRIFT}" font-size="9" font-weight="700" fill="#8e8e93" text-anchor="middle">5 l</text>
<path d="M78 112 A24 24 0 0 1 122 112" fill="none" stroke="url(#{k}-t)" stroke-width="5" stroke-linecap="round"/>
<circle cx="100" cy="106" r="16" fill="#eef0f3" stroke="#aab0b9" stroke-width="2"/><path d="M100 106 L110 96" stroke="#ff453a" stroke-width="2.6" stroke-linecap="round"/>
<circle cx="100" cy="142" r="3.5" fill="#ff9f0a"/>{_glanz(62, 46, 112)}''', defs)


def durchlauferhitzer():
    k = "dl"
    defs = _weiss(f"{k}-k")
    return _svg(k, _schatten(k, 46, 186) + f'''
<path d="M82 150 V182" stroke="#0a84ff" stroke-width="7" stroke-linecap="round"/><path d="M118 150 V182" stroke="#ff453a" stroke-width="7" stroke-linecap="round"/>
<rect x="76" y="160" width="12" height="8" rx="2" fill="#aeb5bf"/><rect x="112" y="160" width="12" height="8" rx="2" fill="#aeb5bf"/>
<rect x="56" y="18" width="88" height="134" rx="15" fill="url(#{k}-k)" stroke="#c4c9d1"/>
{_anzeige(70, 36, 60, 30, "38°", "#ff9f0a", 17)}
<circle cx="86" cy="82" r="5.5" fill="#e3e6ea" stroke="#c4c9d1"/><circle cx="114" cy="82" r="5.5" fill="#e3e6ea" stroke="#c4c9d1"/>
<path d="M84 82 H88 M112 82 H116 M114 80 V84" stroke="#8e8e93" stroke-width="1.6" stroke-linecap="round"/>
{_blitz(100, 116, 1.25)}{_glanz(62, 24, 122)}''', defs)


# ---------------------------------------------------------------- Heizen und Kühlen

def oelradiator():
    k = "or"
    defs = _weiss(f"{k}-k")
    rippen = "".join(f'<rect x="{x}" y="50" width="13" height="120" rx="6.5" fill="url(#{k}-k)" stroke="#c4c9d1"/>' for x in range(54, 166, 15))
    return _svg(k, _wellen((80, 106, 132), 42, "#ff9f0a") + _schatten(k, 72, 186) + f'''
<rect x="52" y="160" width="118" height="7" rx="3.5" fill="#aeb5bf"/>{rippen}
<rect x="28" y="76" width="24" height="52" rx="6" fill="#eef0f3" stroke="#c4c9d1"/>
{_knopf(40, 92, 6.5)}<circle cx="40" cy="114" r="3.5" fill="#ff9f0a"/>
<circle cx="62" cy="178" r="6" fill="#3a3a3c"/><circle cx="160" cy="178" r="6" fill="#3a3a3c"/>''', defs)


def klimageraet():
    k = "kg"
    defs = _weiss(f"{k}-k")
    schlitze = "".join(f'<path d="M76 {y} H124" stroke="#c4c9d1" stroke-width="2.4" stroke-linecap="round"/>' for y in range(44, 66, 5))
    return _svg(k, _wellen((84, 100, 116), 30, "#64d2ff", 5) + _schatten(k, 52) + f'''
<path d="M136 126 C170 126 176 96 184 62" fill="none" stroke="#c4c9d1" stroke-width="15" stroke-linecap="round"/>
<path d="M136 126 C170 126 176 96 184 62" fill="none" stroke="#aeb5bf" stroke-width="15" stroke-dasharray="2 4"/>
<rect x="62" y="34" width="76" height="146" rx="18" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="72" y="40" width="56" height="28" rx="7" fill="#eef0f3"/>{schlitze}
{_anzeige(80, 78, 40, 18, "22°", "#64d2ff", 11)}
<g stroke="#64d2ff" stroke-width="2.6" stroke-linecap="round"><path d="M100 108 V132 M89.6 114 L110.4 126 M89.6 126 L110.4 114"/></g>
<circle cx="76" cy="182" r="4.5" fill="#3a3a3c"/><circle cx="124" cy="182" r="4.5" fill="#3a3a3c"/>{_glanz(68, 42, 130)}''', defs)


def ventilator():
    k = "ve"
    import math
    defs = _metall(f"{k}-m") + _linear(f"{k}-f", [(0, "#9fdcff"), (1, "#3a9bf0")])
    speichen = "".join(
        f'<path d="M{100 + 16 * math.cos(math.radians(a)):.1f} {80 + 16 * math.sin(math.radians(a)):.1f} '
        f'L{100 + 62 * math.cos(math.radians(a)):.1f} {80 + 62 * math.sin(math.radians(a)):.1f}" stroke="#aeb5bf" stroke-width="1" opacity=".55"/>'
        for a in range(0, 360, 15))
    fluegel = "".join(f'<path transform="rotate({w} 100 80)" d="M100 80 C88 54 104 30 120 40 C132 50 118 70 100 80 Z" fill="url(#{k}-f)" opacity=".92"/>'
                      for w in (0, 120, 240))
    return _svg(k, _schatten(k, 46, 182) + f'''
<rect x="96" y="128" width="8" height="48" fill="url(#{k}-m)"/>
<ellipse cx="100" cy="178" rx="40" ry="8" fill="#c4c9d1"/><ellipse cx="100" cy="175" rx="40" ry="8" fill="#e3e6ea"/>
<circle cx="100" cy="80" r="62" fill="#f5f5f7" opacity=".55"/>{fluegel}{speichen}
<circle cx="100" cy="80" r="62" fill="none" stroke="#c4c9d1" stroke-width="3.5"/>
<circle cx="100" cy="80" r="44" fill="none" stroke="#c4c9d1" stroke-width="1.2" opacity=".6"/>
<circle cx="100" cy="80" r="10" fill="#fff" stroke="#aeb5bf" stroke-width="2"/>''', defs)


def luftentfeuchter():
    k = "le"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-w", [(0, "#64d2ff"), (1, "#0a64c8")], 0, 1)
    schlitze = "".join(f'<path d="M70 {y} H130" stroke="#c4c9d1" stroke-width="2.4" stroke-linecap="round"/>' for y in range(40, 56, 5))
    return _svg(k, _schatten(k, 52) + f'''
<rect x="56" y="30" width="88" height="150" rx="16" fill="url(#{k}-k)" stroke="#c4c9d1"/>{schlitze}
{_anzeige(76, 62, 48, 18, "55%", "#64d2ff", 10)}
<path d="M100 88 C94 98 90 102 90 108 A10 10 0 0 0 110 108 C110 102 106 98 100 88 Z" fill="#0a84ff"/>
<rect x="66" y="124" width="68" height="48" rx="8" fill="#e9f4ff" stroke="#c4c9d1"/>
<path d="M66 146 Q83 140 100 146 T134 146 V164 Q134 172 126 172 H74 Q66 172 66 164 Z" fill="url(#{k}-w)" opacity=".85"/>
{_glanz(62, 36, 134)}''', defs)


def infrarotheizung():
    k = "ih"
    defs = _weiss(f"{k}-k") + _radial(f"{k}-g", [(0, "#ff9f0a", .28), (1, "#ff9f0a", 0)])
    return _svg(k, f'''<rect x="34" y="42" width="144" height="108" rx="6" fill="#000" opacity=".08"/>
<rect x="28" y="36" width="144" height="108" rx="6" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<ellipse cx="100" cy="90" rx="80" ry="60" fill="url(#{k}-g)"/>
<rect x="34" y="42" width="5" height="96" rx="2.5" fill="#fff" opacity=".8"/>''' + _wellen((64, 100, 136), 186, "#ff6a1f", 8) + f'''
<path d="M164 144 V160 Q164 168 172 168 H182" fill="none" stroke="#c4c9d1" stroke-width="3"/>''', defs)


def handtuchheizkoerper():
    k = "ht"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-t", [(0, "#64d2ff"), (1, "#0a6fd6")], 0, 1)
    sprossen = "".join(f'<rect x="56" y="{y}" width="88" height="6" rx="3" fill="#eef0f3" stroke="#c4c9d1"/>' for y in range(34, 176, 16))
    return _svg(k, _schatten(k, 56) + sprossen + f'''
<rect x="50" y="18" width="12" height="166" rx="6" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="138" y="18" width="12" height="166" rx="6" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<path d="M70 70 H130 V134 Q130 140 124 140 H76 Q70 140 70 134 Z" fill="url(#{k}-t)"/>
<rect x="68" y="62" width="64" height="12" rx="5" fill="#9fdcff"/>
<path d="M70 124 H130 M70 129 H130" stroke="#fff" stroke-width="2" opacity=".6"/>''' + _wellen((168, 180), 120, "#ff9f0a", 7), defs)


def infrarotkabine():
    k = "ik"
    defs = (_linear(f"{k}-h", [(0, "#e2ac72"), (1, "#a8683a")])
            + _radial(f"{k}-g", [(0, "#ff8a4a", 1), (.7, "#c2340f", 1), (1, "#5a1200", 1)], "50%", "40%", "80%"))
    bretter = "".join(f'<path d="M{x} 36 V176" stroke="#7a4522" stroke-width="1" opacity=".35"/>' for x in range(46, 166, 12))
    return _svg(k, _schatten(k, 76, 186) + f'''
<rect x="34" y="32" width="132" height="148" rx="6" fill="url(#{k}-h)"/>{bretter}
<rect x="30" y="26" width="140" height="11" rx="4" fill="#7a4522"/>
<rect x="74" y="50" width="60" height="124" rx="6" fill="url(#{k}-g)" stroke="#5a3a20" stroke-width="2.5"/>
<rect x="80" y="128" width="48" height="6" rx="2" fill="#a8683a" opacity=".8"/>
<rect x="124" y="104" width="4" height="26" rx="2" fill="#d5d9df"/>
{_anzeige(40, 50, 28, 14, "45°", "#ff9f0a", 8)}
<polygon points="74,50 102,50 82,174 74,174" fill="#fff" opacity=".12"/>''', defs)


# ---------------------------------------------------------------- Büro, Technik, Unterhaltung

def gaming_pc():
    k = "pc"
    defs = (_dunkel(f"{k}-k") + _linear(f"{k}-r", [(0, "#ff375f"), (.5, "#bf5af2"), (1, "#0a84ff")], 0, 1)
            + f'<filter id="{k}-f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>')
    luefter = "".join(
        f'<circle cx="96" cy="{y}" r="18" fill="#141418" stroke="url(#{k}-r)" stroke-width="4"/>'
        f'<circle cx="96" cy="{y}" r="5.5" fill="#2c2c2e"/>'
        f'<path d="M96 {y - 13} Q104 {y - 6} 96 {y} M109 {y + 6} Q100 {y + 8} 96 {y} M83 {y + 6} Q88 {y - 2} 96 {y}" fill="none" stroke="#48484a" stroke-width="2.5"/>'
        for y in (62, 104, 146))
    return _svg(k, _schatten(k, 54) + f'''
<rect x="52" y="20" width="96" height="164" rx="10" fill="url(#{k}-k)"/>
<rect x="60" y="28" width="72" height="148" rx="6" fill="#0b0b10" stroke="#3a3a3c"/>
<g filter="url(#{k}-f)" opacity=".7"><circle cx="96" cy="70" r="22" fill="#bf5af2"/><circle cx="96" cy="140" r="22" fill="#0a84ff"/></g>
{luefter}
<rect x="137" y="28" width="4" height="148" rx="2" fill="url(#{k}-r)"/>
<polygon points="60,28 90,28 70,176 60,176" fill="#fff" opacity=".06"/>''', defs)


def laptop():
    k = "lt"
    defs = (_metall(f"{k}-m") + _linear(f"{k}-w", [(0, "#5e5ce6"), (.55, "#ff375f"), (1, "#ff9f0a")])
            + f'<clipPath id="{k}-c"><rect x="42" y="42" width="116" height="76" rx="3"/></clipPath>'
            + f'<filter id="{k}-f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>')
    return _svg(k, _schatten(k, 84, 150) + f'''
<rect x="36" y="36" width="128" height="88" rx="8" fill="#1d1d1f"/>
<rect x="42" y="42" width="116" height="76" rx="3" fill="url(#{k}-w)"/>
<g clip-path="url(#{k}-c)" filter="url(#{k}-f)"><circle cx="70" cy="60" r="26" fill="#64d2ff" opacity=".7"/><circle cx="140" cy="110" r="24" fill="#ffd60a" opacity=".6"/></g>
<rect x="94" y="36" width="12" height="4" rx="2" fill="#000"/>
<path d="M24 124 H176 L184 138 Q185 143 179 143 H21 Q15 143 16 138 Z" fill="url(#{k}-m)"/>
<rect x="86" y="124" width="28" height="4" rx="2" fill="#9aa1ab"/>''', defs)


def monitor():
    k = "mo"
    defs = _metall(f"{k}-m") + _linear(f"{k}-w", [(0, "#ffb340"), (1, "#ff375f")])
    return _svg(k, _schatten(k, 56, 182) + f'''
<path d="M88 132 L82 172 H118 L112 132 Z" fill="url(#{k}-m)"/>
<rect x="66" y="170" width="68" height="7" rx="3.5" fill="#aeb5bf"/>
<rect x="18" y="26" width="164" height="108" rx="9" fill="#d5d9df"/>
<rect x="22" y="30" width="156" height="100" rx="6" fill="#1d1d1f"/>
<rect x="26" y="34" width="148" height="92" rx="3" fill="url(#{k}-w)"/>
<rect x="38" y="46" width="70" height="50" rx="5" fill="#fff" opacity=".92"/><rect x="38" y="46" width="70" height="9" rx="4" fill="#e3e6ea"/>
<circle cx="44" cy="50.5" r="1.8" fill="#ff453a"/><circle cx="50" cy="50.5" r="1.8" fill="#ffd60a"/><circle cx="56" cy="50.5" r="1.8" fill="#30d158"/>
<rect x="44" y="62" width="40" height="4" rx="2" fill="#c4c9d1"/><rect x="44" y="70" width="56" height="4" rx="2" fill="#c4c9d1"/><rect x="44" y="78" width="30" height="4" rx="2" fill="#c4c9d1"/>
<rect x="116" y="60" width="48" height="42" rx="5" fill="#fff" opacity=".85"/><rect x="122" y="80" width="8" height="16" rx="1.5" fill="#0a84ff"/>
<rect x="134" y="72" width="8" height="24" rx="1.5" fill="#30d158"/><rect x="146" y="86" width="8" height="10" rx="1.5" fill="#ff9f0a"/>
<rect x="66" y="114" width="68" height="8" rx="4" fill="#fff" opacity=".45"/>''', defs)


def wlan_router():
    k = "wr"
    defs = _weiss(f"{k}-k")
    return _svg(k, _bogen(100, 84, (12, 26, 40), "#0a84ff", 5) + f'<circle cx="100" cy="84" r="4.5" fill="#0a84ff"/>' + _schatten(k, 74, 160) + f'''
<rect x="50" y="64" width="9" height="58" rx="4.5" fill="#3a3a3c" transform="rotate(-10 54 120)"/>
<rect x="141" y="64" width="9" height="58" rx="4.5" fill="#3a3a3c" transform="rotate(10 146 120)"/>
<polygon points="38,116 60,98 140,98 162,116" fill="#f5f5f7" stroke="#c4c9d1" stroke-linejoin="round"/>
<rect x="34" y="116" width="132" height="32" rx="8" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<circle cx="58" cy="132" r="3.2" fill="#30d158"/><circle cx="72" cy="132" r="3.2" fill="#30d158"/><circle cx="86" cy="132" r="3.2" fill="#0a84ff"/>
<circle cx="100" cy="132" r="3.2" fill="#30d158"/><rect x="126" y="129" width="26" height="6" rx="3" fill="#e3e6ea"/>''', defs)


def smartphone():
    k = "sp"
    defs = _linear(f"{k}-w", [(0, "#5e5ce6"), (.55, "#bf5af2"), (1, "#ff375f")], 0.6, 1)
    return _svg(k, _schatten(k, 46) + f'''
<path d="M100 164 V176 Q100 186 112 186 H150" fill="none" stroke="#c4c9d1" stroke-width="6" stroke-linecap="round"/>
<path d="M100 164 V176 Q100 186 112 186 H150" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round"/>
<rect x="62" y="12" width="76" height="154" rx="17" fill="#1d1d1f"/>
<rect x="66" y="16" width="68" height="146" rx="14" fill="url(#{k}-w)"/>
<rect x="88" y="22" width="24" height="8" rx="4" fill="#000"/>
<text x="100" y="62" font-family="{SCHRIFT}" font-size="22" font-weight="700" fill="#fff" text-anchor="middle">9:41</text>
<circle cx="100" cy="112" r="20" fill="#fff" opacity=".22"/>{_blitz(100, 112, 1.1, "#30d158")}
<rect x="84" y="152" width="32" height="3.5" rx="1.75" fill="#fff" opacity=".8"/>''', defs)


def drucker():
    k = "dr"
    defs = _weiss(f"{k}-k")
    return _svg(k, _schatten(k, 80, 182) + f'''
<rect x="56" y="22" width="88" height="44" rx="2" fill="#fff" stroke="#d5d9df"/>
<path d="M66 32 H120 M66 40 H134 M66 48 H110" stroke="#d5d9df" stroke-width="3" stroke-linecap="round"/>
<rect x="26" y="56" width="148" height="84" rx="14" fill="url(#{k}-k)" stroke="#c4c9d1"/>
{_anzeige(38, 68, 36, 20, "OK", "#30d158", 9)}
<circle cx="140" cy="78" r="4.5" fill="#32ade6"/><circle cx="152" cy="78" r="4.5" fill="#ff2d92"/><circle cx="164" cy="78" r="4.5" fill="#ffd60a"/>
<rect x="48" y="108" width="104" height="9" rx="4.5" fill="#3a3a3c"/>
<polygon points="54,114 146,114 158,172 42,172" fill="#fff" stroke="#d5d9df"/>
<rect x="62" y="124" width="40" height="22" rx="3" fill="#0a84ff" opacity=".85"/><rect x="106" y="124" width="30" height="22" rx="3" fill="#ff9f0a" opacity=".85"/>
<path d="M60 154 H140 M58 162 H120" stroke="#c4c9d1" stroke-width="3" stroke-linecap="round"/>{_glanz(32, 62, 70)}''', defs)


def beamer():
    k = "bm"
    defs = (_weiss(f"{k}-k") + _linear(f"{k}-l", [(0, "#fff3c4"), (1, "#fff3c4")], 1, 0)
            + f'<linearGradient id="{k}-s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffe9a8" stop-opacity=".75"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></linearGradient>'
            + _radial(f"{k}-o", [(0, "#7d7aff", 1), (1, "#1d1d3a", 1)]))
    schlitze = "".join(f'<rect x="{x}" y="94" width="3" height="28" rx="1.5" fill="#d5d9df"/>' for x in range(36, 66, 7))
    return _svg(k, f'<polygon points="126,98 200,52 200,166 126,118" fill="url(#{k}-s)"/>' + _schatten(k, 66, 158) + f'''
<rect x="20" y="78" width="118" height="60" rx="16" fill="url(#{k}-k)" stroke="#c4c9d1"/>{schlitze}
<circle cx="112" cy="108" r="21" fill="#1d1d1f" stroke="#9aa1ab" stroke-width="4"/>
<circle cx="112" cy="108" r="13" fill="url(#{k}-o)"/><circle cx="107" cy="103" r="3.5" fill="#fff" opacity=".7"/>
<rect x="60" y="74" width="22" height="5" rx="2.5" fill="#c4c9d1"/>
<rect x="30" y="138" width="12" height="6" rx="2" fill="#8e959f"/><rect x="116" y="138" width="12" height="6" rx="2" fill="#8e959f"/>''', defs)


def soundbar():
    k = "sb"
    defs = (_dunkel(f"{k}-k") + f'<pattern id="{k}-p" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1.2" fill="#55555a"/></pattern>')
    note = ('<g fill="{f}"><ellipse cx="{x}" cy="{y}" rx="7" ry="5.5" transform="rotate(-20 {x} {y})"/>'
            '<rect x="{sx}" y="{sy}" width="3" height="30" rx="1"/><path d="M{sx} {sy} q12 4 14 16 q-4 -8 -14 -8 Z"/></g>')
    noten = (note.format(f="#bf5af2", x=74, y=74, sx=78.5, sy=44) + note.format(f="#0a84ff", x=124, y=62, sx=128.5, sy=32))
    return _svg(k, noten + _schatten(k, 92, 150) + f'''
<rect x="8" y="104" width="184" height="36" rx="18" fill="url(#{k}-k)"/>
<rect x="18" y="111" width="164" height="22" rx="11" fill="url(#{k}-p)"/>
<rect x="88" y="134" width="24" height="2.5" rx="1.25" fill="#fff" opacity=".85"/>
<path d="M24 110 H176" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".12"/>''', defs)


def drucker_3d():
    k = "d3"
    defs = _linear(f"{k}-o", [(0, "#ffb340"), (1, "#ff6a1f")], 0, 1) + _metall(f"{k}-m")
    schichten = "".join(f'<path d="M{86 + abs(y - 128) * .14:.1f} {y} H{114 - abs(y - 128) * .14:.1f}" stroke="#fff" stroke-width="1" opacity=".3"/>'
                        for y in range(112, 150, 4))
    return _svg(k, _schatten(k, 76, 186) + f'''
<circle cx="24" cy="70" r="15" fill="#30d158"/><circle cx="24" cy="70" r="5" fill="#1d1d1f"/>
<path d="M34 62 Q60 40 96 74" fill="none" stroke="#30d158" stroke-width="1.6"/>
<rect x="36" y="22" width="9" height="150" rx="3" fill="#2c2c2e"/><rect x="155" y="22" width="9" height="150" rx="3" fill="#2c2c2e"/>
<rect x="36" y="20" width="128" height="10" rx="4" fill="#2c2c2e"/>
<rect x="40" y="80" width="120" height="7" rx="3" fill="url(#{k}-m)"/>
<rect x="88" y="70" width="26" height="24" rx="4" fill="#1d1d1f"/><circle cx="101" cy="80" r="5" fill="#3a3a3c"/>
<path d="M97 94 H105 L101 102 Z" fill="#c4c9d1"/>
<path d="M88 150 Q84 128 92 116 Q96 108 96 104 H106 Q106 108 110 116 Q118 128 112 150 Z" fill="url(#{k}-o)"/>{schichten}
<polygon points="50,150 150,150 158,162 42,162" fill="#48484a"/>
<rect x="30" y="164" width="140" height="18" rx="5" fill="#1d1d1f"/><rect x="44" y="169" width="26" height="8" rx="2" fill="#0a84ff"/>''', defs)


# ---------------------------------------------------------------- Licht

def gluehbirne():
    k = "gb"
    defs = (_radial(f"{k}-g", [(0, "#fff7e0", .95), (.6, "#ffe0a0", .55), (1, "#ffcf70", .35)], "45%", "40%", "65%")
            + _radial(f"{k}-gl", [(0, "#ff9f0a", .5), (1, "#ff9f0a", 0)]))
    return _svg(k, f'<circle cx="100" cy="78" r="82" fill="url(#{k}-gl)"/>' + _schatten(k, 34, 190) + f'''
<path d="M100 20 C63 20 43 49 45 79 C47 103 63 116 70 130 L130 130 C137 116 153 103 155 79 C157 49 137 20 100 20 Z" fill="url(#{k}-g)" stroke="#e8c27a" stroke-opacity=".7"/>
<path d="M92 128 L90 92 M108 128 L110 92" stroke="#9aa1ab" stroke-width="1.6"/>
<path d="M90 92 l3 -6 l3 6 l3 -6 l3 6 l3 -6 l3 6 l3 -6 l3 6" fill="none" stroke="#ff6a00" stroke-width="2.6" stroke-linejoin="round"/>
<path d="M70 52 C76 38 88 32 98 31" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".8"/>
<rect x="70" y="130" width="60" height="11" rx="3" fill="#d5d9df"/>
<rect x="72" y="143" width="56" height="8" rx="4" fill="#c7a25a"/><rect x="74" y="153" width="52" height="8" rx="4" fill="#b8924a"/><rect x="78" y="163" width="44" height="8" rx="4" fill="#a8823a"/>
<circle cx="100" cy="178" r="6" fill="#636366"/>''' + _wellen((32, 168), 120, "#ff6a00", 6), defs)


# ---------------------------------------------------------------- Sonstiges

def aquarium():
    k = "aq"
    defs = _linear(f"{k}-w", [(0, "#7fd4ff"), (1, "#0a5aa8")], 0, 1)
    fisch = ('<g transform="translate({x} {y}) scale({s})"><ellipse cx="0" cy="0" rx="12" ry="7" fill="#ff9f0a"/>'
             '<path d="M10 0 L20 -7 L20 7 Z" fill="#ff7a1f"/><circle cx="-6" cy="-2" r="1.8" fill="#fff"/><path d="M-1 -6 V6" stroke="#fff" stroke-width="2" opacity=".7"/></g>')
    return _svg(k, _schatten(k, 80, 186) + f'''
<rect x="24" y="40" width="152" height="12" rx="4" fill="#2c2c2e"/>
<rect x="24" y="52" width="152" height="112" rx="5" fill="url(#{k}-w)" opacity=".92" stroke="#9fd0ff" stroke-width="2"/>
<polygon points="40,54 64,54 90,164 52,164" fill="#fff" opacity=".08"/><polygon points="110,54 128,54 150,164 120,164" fill="#fff" opacity=".07"/>
<path d="M26 150 Q60 142 100 150 T174 148 V162 Q174 164 172 164 H28 Q26 164 26 162 Z" fill="#d6b98c"/>
<path d="M44 152 C38 130 52 118 44 96 M54 152 C60 132 50 120 58 104 M152 152 C146 132 160 122 154 102" fill="none" stroke="#30d158" stroke-width="5" stroke-linecap="round"/>
{fisch.format(x=100, y=96, s=1.2)}{fisch.format(x=132, y=124, s=.8)}
<circle cx="76" cy="118" r="3" fill="none" stroke="#fff" stroke-width="1.4" opacity=".7"/><circle cx="80" cy="100" r="2.2" fill="none" stroke="#fff" stroke-width="1.2" opacity=".6"/>
<circle cx="74" cy="84" r="1.6" fill="none" stroke="#fff" stroke-width="1.2" opacity=".5"/>
<rect x="28" y="164" width="144" height="16" rx="3" fill="#3a3a3c"/>''', defs)


def terrarium():
    k = "te"
    defs = (_linear(f"{k}-h", [(0, "#fff6e4"), (1, "#f2d39e")], 0, 1) + _radial(f"{k}-l", [(0, "#ff9f0a", .55), (1, "#ff9f0a", 0)]))
    return _svg(k, _schatten(k, 80, 186) + f'''
<rect x="30" y="42" width="140" height="122" rx="6" fill="url(#{k}-h)"/>
<circle cx="78" cy="48" r="46" fill="url(#{k}-l)"/>
<path d="M32 146 Q70 136 104 144 T168 140 V162 H32 Z" fill="#e3b979"/>
<path d="M36 156 Q36 130 62 128 Q86 128 88 156 Z" fill="#8e959f"/>
<path d="M48 130 Q58 118 72 124 Q80 128 84 122" fill="none" stroke="#2f9e44" stroke-width="5" stroke-linecap="round"/>
<circle cx="86" cy="121" r="4.5" fill="#2f9e44"/><path d="M48 130 Q36 136 30 132" fill="none" stroke="#2f9e44" stroke-width="3" stroke-linecap="round"/>
<path d="M142 150 V110 Q142 102 148 102 Q154 102 154 110 V150 Z M142 128 H134 Q130 128 130 122 V114 M154 120 H160 Q164 120 164 114 V108" fill="#30d158" stroke="#30d158" stroke-width="3" stroke-linejoin="round"/>
<rect x="30" y="42" width="140" height="122" rx="6" fill="#eaf6ff" opacity=".18" stroke="#9fd0ff" stroke-width="2"/>
<rect x="38" y="30" width="124" height="13" rx="4" fill="#2c2c2e"/><rect x="62" y="42" width="32" height="5" rx="2" fill="#ffcf70"/>
<rect x="26" y="164" width="148" height="14" rx="4" fill="#8a5530"/>
<polygon points="34,46 52,46 70,162 40,162" fill="#fff" opacity=".12"/>''', defs)


def poolpumpe():
    k = "pp"
    defs = _linear(f"{k}-w", [(0, "#7fe0ff"), (1, "#0a84ff")], 0, 1) + _linear(f"{k}-r", [(0, "#e3e6ea"), (1, "#aeb5bf")], 0, 1)
    return _svg(k, _schatten(k, 90, 182) + f'''
<path d="M16 96 V150 Q16 172 86 172 Q156 172 156 150 V96 Z" fill="url(#{k}-r)"/>
<path d="M16 130 Q16 150 86 150 Q156 150 156 130" fill="none" stroke="#0a84ff" stroke-width="4" opacity=".5"/>
<ellipse cx="86" cy="96" rx="70" ry="22" fill="url(#{k}-w)" stroke="#d5d9df" stroke-width="3"/>
<path d="M48 94 Q58 88 68 94 M96 102 Q106 96 116 102 M80 86 Q88 82 96 86" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>
<path d="M150 112 Q166 112 170 140" fill="none" stroke="#8e959f" stroke-width="6"/>
<rect x="156" y="138" width="38" height="36" rx="10" fill="#3a3a3c"/><ellipse cx="175" cy="138" rx="19" ry="5" fill="#55555a"/>
<circle cx="184" cy="160" r="3" fill="#30d158"/>''', defs)


def teichpumpe():
    k = "tp"
    defs = _linear(f"{k}-w", [(0, "#4fc3c7"), (1, "#0a5a6a")], 0, 1)
    tropfen = "".join(f'<circle cx="{x}" cy="{y}" r="2.4" fill="#9fe0ff"/>' for x, y in ((70, 112), (130, 110), (60, 128), (140, 126), (92, 60), (108, 58)))
    steine = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="6" fill="#aeb5bf" stroke="#8e959f"/>'
                     for x, y in ((26, 150), (44, 166), (74, 176), (110, 177), (146, 170), (172, 156)) for rx in (11,))
    return _svg(k, f'''
<ellipse cx="100" cy="152" rx="80" ry="26" fill="url(#{k}-w)"/>{steine}
<ellipse cx="100" cy="148" rx="18" ry="5" fill="none" stroke="#fff" stroke-width="1.6" opacity=".6"/>
<ellipse cx="100" cy="150" rx="32" ry="9" fill="none" stroke="#fff" stroke-width="1.4" opacity=".4"/>
<path d="M100 146 Q100 70 100 56" stroke="#9fe0ff" stroke-width="5" stroke-linecap="round" fill="none"/>
<path d="M100 60 Q76 64 66 142 M100 60 Q124 64 134 142 M100 60 Q86 70 82 140 M100 60 Q114 70 118 140" fill="none" stroke="#64d2ff" stroke-width="2.6" stroke-linecap="round" opacity=".8"/>
{tropfen}
<path d="M52 160 A13 5 0 1 1 64 164 L56 160 Z" fill="#30d158"/><circle cx="150" cy="158" r="5" fill="#ff7ab0"/><circle cx="150" cy="158" r="2" fill="#ffd60a"/>''', defs)


def e_bike():
    k = "eb"
    import math
    def rad(cx):
        speichen = "".join(f'<path d="M{cx} 140 L{cx + 28 * math.cos(math.radians(a)):.1f} {140 + 28 * math.sin(math.radians(a)):.1f}" stroke="#aeb5bf" stroke-width="1"/>'
                           for a in range(0, 360, 30))
        return (f'<circle cx="{cx}" cy="140" r="33" fill="none" stroke="#1d1d1f" stroke-width="6"/>'
                f'<circle cx="{cx}" cy="140" r="28" fill="none" stroke="#8e959f" stroke-width="1.5"/>{speichen}<circle cx="{cx}" cy="140" r="4" fill="#48484a"/>')
    return _svg(k, _schatten(k, 88, 178) + rad(52) + rad(148) + f'''
<path d="M52 140 L98 140 L86 90 L52 140 M86 92 L136 88 L98 140 M136 88 L148 140" fill="none" stroke="#2c2c2e" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
<path d="M104 128 L128 100" stroke="#3a3a3c" stroke-width="13" stroke-linecap="round"/>
<circle cx="116" cy="114" r="3" fill="#30d158"/>
<path d="M74 82 H98 Q100 77 95 77 H78 Q72 77 74 82 Z" fill="#1d1d1f"/><path d="M86 82 V92" stroke="#2c2c2e" stroke-width="4"/>
<path d="M136 88 L132 70 H148" fill="none" stroke="#2c2c2e" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="98" cy="140" r="7" fill="#48484a"/><path d="M98 140 L106 150" stroke="#2c2c2e" stroke-width="4" stroke-linecap="round"/>
<circle cx="168" cy="48" r="14" fill="#30d158"/>{_blitz(168, 48, .75, "#fff")}''')


def elektroauto():
    k = "ea"
    defs = (_linear(f"{k}-k", [(0, "#ffffff"), (1, "#c9ced6")], 0, 1) + _linear(f"{k}-f", [(0, "#4a5059"), (1, "#16191d")], 0, 1)
            + _metall(f"{k}-m"))
    def rad(cx):
        return (f'<circle cx="{cx}" cy="138" r="19" fill="#1d1d1f"/><circle cx="{cx}" cy="138" r="11.5" fill="url(#{k}-m)"/>'
                f'<circle cx="{cx}" cy="138" r="3" fill="#636366"/>')
    return _svg(k, _schatten(k, 92, 160) + f'''
<path d="M30 118 Q8 126 12 170" fill="none" stroke="#2c2c2e" stroke-width="4" stroke-linecap="round"/>
<path d="M18 132 Q16 114 34 110 L62 104 Q84 78 114 76 H128 Q152 78 168 102 L180 106 Q190 110 190 122 V132 Q190 140 182 140 H24 Q18 140 18 132 Z" fill="url(#{k}-k)" stroke="#aeb5bf"/>
<path d="M68 104 Q86 84 112 83 H126 Q144 84 156 102 Z" fill="url(#{k}-f)"/>
<path d="M114 83 V104" stroke="#fff" stroke-width="3"/>
<path d="M176 112 L186 114 Q187 118 182 118 L174 117 Z" fill="#64d2ff"/><path d="M20 118 H28 V124 H19 Z" fill="#ff453a"/>
<path d="M30 116 h4 v6 h-4 z" fill="#30d158"/>
{rad(54)}{rad(154)}
<circle cx="100" cy="40" r="15" fill="#30d158"/>{_blitz(100, 40, .8, "#fff")}''', defs)


def maehroboter():
    k = "mr"
    defs = _linear(f"{k}-g", [(0, "#5fd16b"), (1, "#248a3d")], 0, 1) + _dunkel(f"{k}-k")
    halme = "".join(f'<path d="M{x} 156 l{(-3, 2, -1, 3)[x % 4]} -9" stroke="#2f9e44" stroke-width="2.4" stroke-linecap="round"/>' for x in range(14, 190, 7))
    return _svg(k, f'''<rect x="8" y="152" width="184" height="34" rx="12" fill="url(#{k}-g)"/>{halme}
<path d="M34 148 Q30 120 58 108 L118 92 Q154 88 170 114 Q178 128 172 140 Q168 150 156 150 H40 Q34 150 34 148 Z" fill="url(#{k}-k)"/>
<path d="M60 110 L118 96 Q148 92 162 112" fill="none" stroke="#c5f04a" stroke-width="5" stroke-linecap="round"/>
<circle cx="114" cy="104" r="6.5" fill="#ff453a"/>
<rect x="128" y="112" width="22" height="8" rx="3" fill="#0d0d0f"/><circle cx="134" cy="116" r="1.8" fill="#30d158"/>
<circle cx="62" cy="148" r="20" fill="#1d1d1f"/><circle cx="62" cy="148" r="11" fill="#48484a"/>
<circle cx="154" cy="152" r="8" fill="#1d1d1f"/><circle cx="154" cy="152" r="3" fill="#48484a"/>''', defs)


def foehn():
    k = "fo"
    defs = _linear(f"{k}-k", [(0, "#ff8fa3"), (1, "#e0405a")], 0, 1)
    return _svg(k, f'''<path d="M168 66 H194 M170 78 H198 M168 90 H192" stroke="#a1a1a6" stroke-width="3" stroke-linecap="round" stroke-dasharray="6 5" opacity=".6"/>'''
                + _schatten(k, 46, 186) + f'''
<path d="M96 168 Q100 186 120 184" fill="none" stroke="#c4c9d1" stroke-width="4" stroke-linecap="round"/>
<path d="M78 96 L100 96 L106 162 Q106 170 98 170 H94 Q86 170 86 162 Z" fill="url(#{k}-k)"/>
<rect x="90" y="112" width="8" height="16" rx="3" fill="#fff" opacity=".85"/>
<rect x="58" y="52" width="94" height="48" rx="24" fill="url(#{k}-k)"/>
<rect x="146" y="60" width="20" height="32" rx="5" fill="#2c2c2e"/>
<circle cx="62" cy="76" r="30" fill="url(#{k}-k)"/>
<circle cx="62" cy="76" r="20" fill="#f5f5f7" stroke="#e3e6ea"/>
<circle cx="62" cy="76" r="13" fill="none" stroke="#c4c9d1" stroke-width="2"/><circle cx="62" cy="76" r="6" fill="#c4c9d1"/>
<path d="M76 58 H140" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".45"/>''', defs)


def zahnbuerste():
    k = "zb"
    defs = _weiss(f"{k}-k")
    borsten = "".join(f'<rect x="106" y="{y}" width="9" height="3" rx="1.5" fill="{c}"/>' for y, c in zip(range(19, 41, 4), ("#64d2ff", "#fff", "#64d2ff", "#fff", "#64d2ff", "#fff")))
    return _svg(k, _schatten(k, 40, 184) + f'''
<rect x="70" y="162" width="60" height="20" rx="10" fill="url(#{k}-k)" stroke="#c4c9d1"/><circle cx="100" cy="172" r="2.6" fill="#30d158"/>
<rect x="86" y="60" width="28" height="108" rx="14" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="94" y="30" width="12" height="36" rx="6" fill="#fff" stroke="#c4c9d1"/>
<rect x="90" y="14" width="18" height="30" rx="7" fill="#fff" stroke="#c4c9d1"/>{borsten}
<circle cx="100" cy="100" r="6.5" fill="#0a84ff"/><circle cx="96" cy="114" r="1.6" fill="#64d2ff"/><circle cx="100" cy="114" r="1.6" fill="#64d2ff"/><circle cx="104" cy="114" r="1.6" fill="#c4c9d1"/>
<rect x="86" y="132" width="28" height="6" fill="#64d2ff" opacity=".6"/><rect x="90" y="66" width="4" height="96" rx="2" fill="#fff" opacity=".8"/>''', defs)


# ---------------------------------------------------------------- Weitere Spar-Produkte

def topf():
    k = "tf"
    defs = _metall(f"{k}-m") + _linear(f"{k}-d", [(0, "#e8f4ff"), (1, "#b9d7f0")], 0, 1)
    return _svg(k, _wellen((86, 114), 52, "#a1a1a6", 6) + _schatten(k, 66, 182) + f'''
<rect x="30" y="102" width="20" height="9" rx="4" fill="#2c2c2e"/><rect x="150" y="102" width="20" height="9" rx="4" fill="#2c2c2e"/>
<path d="M44 94 H156 V150 Q156 172 134 172 H66 Q44 172 44 150 Z" fill="url(#{k}-m)" stroke="#9aa1ab"/>
<ellipse cx="100" cy="92" rx="60" ry="11" fill="url(#{k}-d)" stroke="#9aa1ab" opacity=".95"/>
<path d="M60 88 Q100 80 140 88" fill="none" stroke="#fff" stroke-width="2.5" opacity=".8"/>
<rect x="92" y="72" width="16" height="10" rx="4" fill="#2c2c2e"/><ellipse cx="100" cy="72" rx="12" ry="4" fill="#3a3a3c"/>
<path d="M52 104 Q50 130 54 158" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".6"/>''', defs)


def steckdose(anzeige=None):
    k = "st" if anzeige is None else "sth"
    defs = _weiss(f"{k}-k")
    oben = (_anzeige(74, 54, 52, 22, anzeige, "#ff9f0a", 12) if anzeige else
            '<rect x="80" y="56" width="40" height="18" rx="9" fill="#30d158"/><circle cx="111" cy="65" r="6.5" fill="#fff"/>')
    return _svg(k, _schatten(k, 46) + f'''
<rect x="92" y="18" width="5" height="18" rx="2" fill="#9aa1ab"/><rect x="103" y="18" width="5" height="18" rx="2" fill="#9aa1ab"/>
<rect x="52" y="32" width="96" height="144" rx="26" fill="url(#{k}-k)" stroke="#c4c9d1"/>{oben}
<circle cx="100" cy="128" r="30" fill="#eef0f3" stroke="#c4c9d1" stroke-width="2"/>
<circle cx="88" cy="128" r="4.5" fill="#7d848e"/><circle cx="112" cy="128" r="4.5" fill="#7d848e"/>
<rect x="96" y="100" width="8" height="5" rx="1.5" fill="#b5bbc4"/><rect x="96" y="151" width="8" height="5" rx="1.5" fill="#b5bbc4"/>
{_glanz(58, 38, 132)}''', defs)


def hygrometer():
    k = "hy"
    import math
    defs = _weiss(f"{k}-k")
    skala = []
    for i in range(21):
        a = math.radians(150 + i * 12)
        r1, r2 = (48, 58) if i % 5 == 0 else (52, 58)
        farbe = "#ff9f0a" if i < 6 else ("#30d158" if i < 15 else "#0a84ff")
        skala.append(f'<path d="M{100 + r1 * math.cos(a):.1f} {100 + r1 * math.sin(a):.1f} L{100 + r2 * math.cos(a):.1f} {100 + r2 * math.sin(a):.1f}" '
                     f'stroke="{farbe}" stroke-width="{3 if i % 5 == 0 else 2}" stroke-linecap="round"/>')
    a = math.radians(150 + 11 * 12)
    return _svg(k, _schatten(k, 56, 182) + f'''
<circle cx="100" cy="100" r="72" fill="url(#{k}-k)" stroke="#c4c9d1" stroke-width="2"/>
<circle cx="100" cy="100" r="64" fill="#fff" stroke="#e3e6ea"/>{"".join(skala)}
<path d="M100 100 L{100 + 44 * math.cos(a):.1f} {100 + 44 * math.sin(a):.1f}" stroke="#1d1d1f" stroke-width="3" stroke-linecap="round"/>
<circle cx="100" cy="100" r="5" fill="#1d1d1f"/>
<text x="100" y="134" font-family="{SCHRIFT}" font-size="17" font-weight="700" fill="#1d1d1f" text-anchor="middle">55%</text>
<path d="M100 144 C97 149 95 151 95 154 A5 5 0 0 0 105 154 C105 151 103 149 100 144 Z" fill="#0a84ff"/>''', defs)


def abdichtung():
    k = "ad"
    defs = _weiss(f"{k}-k") + _linear(f"{k}-s", [(0, "#a1a7b0"), (1, "#7d848e")], 0, 1)
    return _svg(k, _schatten(k, 66, 186) + f'''
<rect x="34" y="16" width="132" height="164" rx="6" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="44" y="26" width="112" height="144" rx="3" fill="url(#{k}-s)"/>
<path d="M58 26 Q54 90 60 170 M84 26 Q80 90 86 170 M126 26 Q130 90 124 170" fill="none" stroke="#fff" stroke-width="2" opacity=".18"/>
<path d="M100 28 V168" stroke="#3a3a3c" stroke-width="3" stroke-dasharray="3 3"/>
<rect x="96" y="60" width="8" height="12" rx="2" fill="#d5d9df"/>
<circle cx="100" cy="128" r="20" fill="#3a3a3c" stroke="#d5d9df" stroke-width="3"/>
<path d="M100 128 C100 160 70 170 46 196" fill="none" stroke="#c4c9d1" stroke-width="16" stroke-linecap="round"/>
<path d="M100 128 C100 160 70 170 46 196" fill="none" stroke="#aeb5bf" stroke-width="16" stroke-dasharray="2 4"/>''', defs)


def handtuch():
    k = "hu"
    defs = _linear(f"{k}-a", [(0, "#ffb3c7"), (1, "#ff6f91")], 0, 1) + _linear(f"{k}-b", [(0, "#9fdcff"), (1, "#3a9bf0")], 0, 1)
    return _svg(k, _schatten(k, 70) + f'''
<rect x="30" y="132" width="140" height="42" rx="14" fill="url(#{k}-b)"/><path d="M30 160 H170" stroke="#fff" stroke-width="3" opacity=".6"/>
<rect x="38" y="94" width="124" height="42" rx="14" fill="url(#{k}-a)"/><path d="M38 122 H162" stroke="#fff" stroke-width="3" opacity=".6"/>
<rect x="46" y="56" width="108" height="42" rx="14" fill="url(#{k}-b)"/><path d="M46 84 H154" stroke="#fff" stroke-width="3" opacity=".6"/>
<path d="M56 64 H140" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".5"/>''', defs)


def wallbox():
    k = "wb"
    defs = _weiss(f"{k}-k")
    return _svg(k, _schatten(k, 56, 184) + f'''
<path d="M100 132 C100 168 150 150 150 176 C150 186 120 186 112 178" fill="none" stroke="#2c2c2e" stroke-width="6" stroke-linecap="round"/>
<circle cx="104" cy="176" r="12" fill="#1d1d1f"/><circle cx="100" cy="172" r="2" fill="#8e959f"/><circle cx="108" cy="172" r="2" fill="#8e959f"/>
<circle cx="104" cy="180" r="2" fill="#8e959f"/>
<rect x="52" y="18" width="96" height="120" rx="22" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<circle cx="100" cy="70" r="24" fill="none" stroke="#30d158" stroke-width="5"/>
{_blitz(100, 70, 1, "#30d158")}
<rect x="80" y="108" width="40" height="8" rx="4" fill="#e3e6ea"/>{_glanz(58, 24, 108)}''', defs)


GERAETE_BILDER = {
    "gefrierschrank": gefrierschrank, "waermepumpentrockner": trockner, "kondenstrockner": lambda: trockner(False),
    "geschirrspueler": geschirrspueler, "kaffeevollautomat": kaffeevollautomat, "backofen": backofen, "elektroherd": elektroherd,
    "heissluftfritteuse": heissluftfritteuse, "mikrowelle": mikrowelle, "oelradiator": oelradiator, "klimageraet": klimageraet,
    "ventilator": ventilator, "luftentfeuchter": luftentfeuchter, "gaming-pc": gaming_pc, "laptop": laptop, "monitor": monitor,
    "wlan-router": wlan_router, "aquarium": aquarium, "e-bike": e_bike, "durchlauferhitzer": durchlauferhitzer,
    "staubsauger": staubsauger, "foehn": foehn, "gluehbirne": gluehbirne, "led-lampe": led, "infrarotkabine": infrarotkabine,
    "poolpumpe": poolpumpe, "3d-drucker": drucker_3d, "weinkuehlschrank": weinkuehlschrank, "toaster": toaster,
    "dunstabzugshaube": dunstabzugshaube, "elektrogrill": elektrogrill, "buegeleisen": buegeleisen, "saugroboter": saugroboter,
    "untertischboiler": untertischboiler, "zahnbuerste": zahnbuerste, "infrarotheizung": infrarotheizung,
    "handtuchheizkoerper": handtuchheizkoerper, "smartphone": smartphone, "drucker": drucker, "beamer": beamer,
    "soundbar": soundbar, "elektroauto": elektroauto, "terrarium": terrarium, "teichpumpe": teichpumpe, "maehroboter": maehroboter,
    "topf": topf, "steckdose": steckdose, "thermostat": lambda: steckdose("21°"), "hygrometer": hygrometer,
    "abdichtung": abdichtung, "handtuch": handtuch, "wallbox": wallbox,
}


def receiver():
    k = "rc"
    defs = _dunkel(f"{k}-k")
    return _svg(k, _schatten(k, 80, 150) + f'''
<polygon points="30,96 52,80 148,80 170,96" fill="#3a3a3c"/>
<rect x="26" y="96" width="148" height="40" rx="8" fill="url(#{k}-k)"/>
{_anzeige(42, 106, 52, 20, "20:15", "#64d2ff", 11)}
<rect x="108" y="113" width="26" height="6" rx="3" fill="#2c2c2e"/><circle cx="152" cy="116" r="3" fill="#ff453a"/>
<path d="M32 98 H168" stroke="#fff" stroke-width="1.5" opacity=".15"/>
<rect x="36" y="136" width="14" height="5" rx="2" fill="#1d1d1f"/><rect x="150" y="136" width="14" height="5" rx="2" fill="#1d1d1f"/>''', defs)


def lautsprecher():
    k = "ls"
    defs = (_linear(f"{k}-k", [(0, "#b9bec6"), (.45, "#eceef1"), (1, "#8e959f")], 1, 0)
            + _linear(f"{k}-r", [(0, "#64d2ff"), (.5, "#5e5ce6"), (1, "#bf5af2")], 1, 0)
            + f'<pattern id="{k}-p" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r="1" fill="#7d848e"/></pattern>')
    koerper = "M62 52 V158 Q62 178 100 178 Q138 178 138 158 V52 Z"
    return _svg(k, _schatten(k, 46, 184) + f'''
<path d="{koerper}" fill="url(#{k}-k)"/><path d="{koerper}" fill="url(#{k}-p)" opacity=".45"/>
<ellipse cx="100" cy="52" rx="38" ry="12" fill="#2c2c2e"/>
<ellipse cx="100" cy="52" rx="29" ry="8.5" fill="none" stroke="url(#{k}-r)" stroke-width="4"/>
<path d="M70 70 V160" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".35"/>''', defs)


def ladegeraet():
    k = "lg"
    defs = _weiss(f"{k}-k")
    return _svg(k, _schatten(k, 40, 178) + f'''
<rect x="84" y="20" width="6" height="22" rx="2" fill="#9aa1ab"/><rect x="110" y="20" width="6" height="22" rx="2" fill="#9aa1ab"/>
<path d="M100 112 V140 Q100 160 120 160 H166" fill="none" stroke="#c4c9d1" stroke-width="6" stroke-linecap="round"/>
<path d="M100 112 V140 Q100 160 120 160 H166" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round"/>
<rect x="66" y="38" width="68" height="76" rx="16" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<circle cx="100" cy="72" r="15" fill="#ff9f0a" opacity=".16"/>{_blitz(100, 72, .8, "#ff9f0a")}
{_glanz(72, 44, 64)}''', defs)


def stromzaehler():
    k = "sz"
    defs = _weiss(f"{k}-k")
    return _svg(k, _schatten(k, 58) + f'''
<rect x="44" y="20" width="112" height="162" rx="12" fill="url(#{k}-k)" stroke="#c4c9d1"/>
<rect x="56" y="34" width="88" height="44" rx="7" fill="#1d1d1f"/>
<text x="100" y="61" font-family="{SCHRIFT}" font-size="18" font-weight="700" fill="#30d158" text-anchor="middle" letter-spacing="1">04285</text>
<text x="100" y="72" font-family="{SCHRIFT}" font-size="7" font-weight="600" fill="#8e8e93" text-anchor="middle">kWh</text>
<circle cx="66" cy="92" r="3.5" fill="#ff453a"/><rect x="76" y="89.5" width="40" height="5" rx="2.5" fill="#d5d9df"/>
<rect x="56" y="104" width="88" height="38" rx="5" fill="#eef0f3" stroke="#d5d9df"/>
<path d="M64 114 H118 M64 123 H134 M64 132 H104" stroke="#c4c9d1" stroke-width="3" stroke-linecap="round"/>
<rect x="44" y="150" width="112" height="32" rx="10" fill="#d5d9df"/>
<circle cx="62" cy="166" r="4" fill="#aeb5bf"/><circle cx="138" cy="166" r="4" fill="#aeb5bf"/>{_glanz(50, 26, 118)}''', defs)


GERAETE_BILDER.update({"receiver": receiver, "lautsprecher": lautsprecher, "ladegeraet": ladegeraet, "stromzaehler": stromzaehler})


BILDER = {
    "kuehlschrank": kuehlschrank, "fernseher": fernseher, "heizluefter": heizluefter, "waschmaschine": waschmaschine,
    "spielkonsole": spielkonsole, "wasserkocher": wasserkocher, "messgeraet": messgeraet, "balkonkraftwerk": balkonkraftwerk,
    "heizdecke": heizdecke, "dusche": sparduschkopf, "leiste": steckdosenleiste, "masterslave": lambda: steckdosenleiste(True),
    "staender": waeschestaender, "zeitschaltuhr": zeitschaltuhr, "led": led, "thermometer": thermometer,
    **GERAETE_BILDER,
}


def alle():
    return {key: fn() for key, fn in BILDER.items()}
