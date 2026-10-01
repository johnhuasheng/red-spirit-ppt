# -*- coding: utf-8 -*-
"""生成 PPT 的 4K 素材：丝绸红底、金色光芒、祥云、金边框、浮雕团徽、华丽扇轮、印章、照片调色与扇面贴图。
设计坐标仍以 1600x900 为基准，输出为 2.4 倍(3840x2160)。"""
import os, math, subprocess, tempfile
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, '_build', 'assets'); os.makedirs(A, exist_ok=True)
HD = os.path.join(ROOT, 'images', 'hd')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
W, H = 3840, 2160
S = W / 1600                                  # 设计稿 -> 4K 倍率
PX, PY, RO, RI = -434, 450, 904, 509          # 扇面几何（设计稿 px）
FAN_THETA = {'night': 60, 'history': 100, 'huabiao': 140, 'gateflags': 180, 'hongqi': 220, 'oath': 260, 'youth': 300, 'party': 340}
rng = np.random.default_rng(11)

def save(name, im, q=93):
    ext = os.path.splitext(name)[1]
    ok, buf = cv2.imencode(ext, im, [cv2.IMWRITE_JPEG_QUALITY, q] if ext == '.jpg' else [cv2.IMWRITE_PNG_COMPRESSION, 6])
    buf.tofile(os.path.join(A, name))

def read(path):
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)

def svg_png(name, svg, w, h):
    """用 Chrome 无头模式把 SVG 渲染成透明 PNG（抗锯齿、渐变、滤镜都靠浏览器）。"""
    d = tempfile.mkdtemp()
    html = os.path.join(d, 'a.html')
    open(html, 'w', encoding='utf-8').write(
        f'<html><body style="margin:0;background:transparent;overflow:hidden">{svg}</body></html>')
    out = os.path.join(A, name)
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    '--default-background-color=00000000', f'--window-size={w},{h}', f'--screenshot={out}',
                    'file:///' + html.replace('\\', '/')], capture_output=True)
    assert os.path.exists(out), name

def hexbgr(h):
    h = h.lstrip('#'); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# =============================================================== 背景：红色丝绸
def silk(c_hi='#e3202a', c_mid='#b10f18', c_lo='#4a0207', seed=0, cx=.5, cy=.38):
    r = np.random.default_rng(seed)
    u = (xx * .82 + yy * .57) / W; v = (-xx * .57 + yy * .82) / W
    h = np.zeros_like(xx)
    for k in range(3):                                     # 几道宽大柔和的缎面褶皱
        f = r.uniform(.7, 1.6); ph = r.uniform(0, 6.3); a = 1.0 / (1 + k * .6)
        warp = .12 * np.sin(v * r.uniform(.8, 1.6) * 6.28 + r.uniform(0, 6))
        h += a * np.sin((u + warp) * f * 6.28 + ph)
    gy, gx = np.gradient(cv2.GaussianBlur(h, (0, 0), 12))
    shade = .5 + np.tanh((gx * -.6 + gy * -.8) * 900) * .5
    spec = np.clip(shade - .7, 0, 1) ** 2 * 3.0
    d = np.sqrt(((xx / W - cx) * 1.25) ** 2 + (yy / H - cy) ** 2)
    vig = np.clip(1 - d * 1.05, 0, 1)[..., None]
    base = hexbgr(c_lo) * (1 - vig) + hexbgr(c_mid) * vig
    im = base * (.72 + .45 * shade[..., None]) + hexbgr(c_hi) * .22 * vig * shade[..., None] + 255 * np.array([.55, .7, 1.0]) * spec[..., None] * .22
    im += r.normal(0, 1.6, im.shape)
    return np.clip(im, 0, 255).astype(np.uint8)

def add_glow(im, cx, cy, rx, ry, color, a):
    g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))[..., None]
    return np.clip(im * (1 - a * g) + hexbgr(color) * a * g + im * a * g * .25, 0, 255).astype(np.uint8)

# =============================================================== 金色光芒
def rays_svg(n=36):
    c = 2000; parts = []
    for k in range(n):
        a0 = k * 360 / n; a1 = a0 + 360 / n * .45
        p = lambda a, r: f'{c + r * math.cos(math.radians(a)):.1f},{c + r * math.sin(math.radians(a)):.1f}'
        parts.append(f'<polygon points="{c},{c} {p(a0, 2000)} {p(a1, 2000)}"/>')
    return f'''<svg width="4000" height="4000" xmlns="http://www.w3.org/2000/svg"><defs>
<radialGradient id="g" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff2c0" stop-opacity=".42"/>
<stop offset=".35" stop-color="#ffd36a" stop-opacity=".16"/><stop offset="1" stop-color="#ffb030" stop-opacity="0"/></radialGradient>
<radialGradient id="c" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff6d8" stop-opacity=".7"/>
<stop offset=".25" stop-color="#ffd36a" stop-opacity=".35"/><stop offset="1" stop-color="#ff9a20" stop-opacity="0"/></radialGradient></defs>
<g fill="url(#g)">{''.join(parts)}</g><circle cx="2000" cy="2000" r="2000" fill="url(#c)"/></svg>'''

# =============================================================== 祥云
def cloud_svg(scale=1.0):
    lobes = [(0, 0, 120), (150, -60, 150), (330, -20, 115), (470, 40, 80), (-120, 50, 80)]
    m = np.zeros((900, 1500), np.uint8); ox, oy = 450, 520
    for x, y, r in lobes: cv2.circle(m, (ox + x, oy + y), r, 255, -1)
    cv2.ellipse(m, (ox + 160, oy + 95), (480, 60), 0, 0, 360, 255, -1)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
    c = cv2.GaussianBlur(c.reshape(-1, 1, 2), (1, 31), 0).reshape(-1, 2)[::6]
    outline = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in c) + ' Z'
    spir = []
    for x, y, r in lobes[:4]:
        pts = []
        for t in np.linspace(0, 1, 120):
            a = math.pi * .9 + t * math.pi * 2.6; rr = r * (.86 - .66 * t)
            pts.append((ox + x + rr * math.cos(a), oy + y + rr * math.sin(a)))
        spir.append('M' + ' L'.join(f'{px:.1f} {py:.1f}' for px, py in pts))
    tail = f'M{ox - 330} {oy + 95} Q{ox - 100} {oy + 160} {ox + 160} {oy + 120} T{ox + 640} {oy + 100}'
    w, h = int(1500 * scale), int(900 * scale)
    return f'''<svg width="{w}" height="{h}" viewBox="0 0 1500 900" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff1b8"/><stop offset=".5" stop-color="#e8b44a"/><stop offset="1" stop-color="#a8701c"/></linearGradient>
<linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe08a" stop-opacity=".30"/><stop offset="1" stop-color="#c88a28" stop-opacity=".08"/></linearGradient></defs>
<path d="{outline}" fill="url(#f)" stroke="url(#g)" stroke-width="9" stroke-linejoin="round"/>
<g fill="none" stroke="url(#g)" stroke-width="8" stroke-linecap="round">{''.join(f'<path d="{p}"/>' for p in spir)}</g>
<path d="{tail}" fill="none" stroke="url(#g)" stroke-width="7" stroke-linecap="round"/></svg>'''

# =============================================================== 金色边框（回纹角花）
def frame_svg():
    m = 64; g = 'url(#g)'
    def corner(x, y, sx, sy):
        L = 210; k = 34
        d = (f'M{x} {y + sy * L} L{x} {y} L{x + sx * L} {y} '
             f'M{x + sx * k} {y + sy * (L - 60)} L{x + sx * k} {y + sy * k} L{x + sx * (L - 60)} {y + sy * k} '
             f'M{x + sx * 2 * k} {y + sy * 2 * k} L{x + sx * 3.2 * k} {y + sy * 2 * k} L{x + sx * 3.2 * k} {y + sy * 3.2 * k} L{x + sx * 2 * k} {y + sy * 3.2 * k} Z')
        return f'<path d="{d}" fill="none" stroke="{g}" stroke-width="7"/>'
    return f'''<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff0b0"/><stop offset=".3" stop-color="#d9a441"/>
<stop offset=".55" stop-color="#fbe39a"/><stop offset=".8" stop-color="#b47b22"/><stop offset="1" stop-color="#f3d27a"/></linearGradient></defs>
<rect x="{m + 26}" y="{m + 26}" width="{W - 2 * m - 52}" height="{H - 2 * m - 52}" fill="none" stroke="{g}" stroke-width="3" opacity=".75"/>
{corner(m, m, 1, 1)}{corner(W - m, m, -1, 1)}{corner(m, H - m, 1, -1)}{corner(W - m, H - m, -1, -1)}</svg>'''

# =============================================================== 浮雕团徽
def emblem_svg(size=2000):
    def P(a, r): t = math.radians(a); return f'{r * math.cos(t):.2f} {r * math.sin(t):.2f}'
    d = f'M{P(150, 100)} A100 100 0 0 1 {P(240, 100)} A100 100 0 0 1 {P(330, 100)} '
    for i in range(12):
        b = -30 + i * 15; d += f'L{P(b + 3, 112)} L{P(b + 10, 112)} L{P(b + 13, 100)} L{P(b + 15, 100)} '
    gear = d + 'Z'
    flag = 'M-66 -108 C-30 -122 10 -88 48 -98 C78 -106 96 -96 110 -80 L114 -14 C96 -30 80 -26 60 -22 C34 -16 18 -2 -6 -12 C-22 -18 -34 -40 -46 -62 Z'
    star = ''
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; rr = 5.6 if i % 2 else 14
        star += ('L' if i else 'M') + f'{-30 + rr * math.cos(a):.2f} {-80 + rr * math.sin(a):.2f} '
    rays = ''.join(f'<line x1="0" y1="78" x2="{110 * math.cos(math.pi + i * math.pi / 16):.1f}" y2="{78 + 110 * math.sin(math.pi + i * math.pi / 16):.1f}"/>' for i in range(17))
    return f'''<svg width="{size}" height="{size}" viewBox="-142 -146 284 284" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="gold" x1="0" y1="0" x2=".9" y2="1"><stop offset="0" stop-color="#fff7c4"/><stop offset=".22" stop-color="#ffd84a"/>
<stop offset=".45" stop-color="#e9a90c"/><stop offset=".62" stop-color="#ffe27a"/><stop offset=".82" stop-color="#c58300"/><stop offset="1" stop-color="#8e5a00"/></linearGradient>
<linearGradient id="red" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff4a3a"/><stop offset=".45" stop-color="#e3000f"/><stop offset="1" stop-color="#8f0008"/></linearGradient>
<filter id="emb" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur in="SourceAlpha" stdDeviation="1.6" result="b"/>
<feSpecularLighting in="b" surfaceScale="3.2" specularConstant="1.1" specularExponent="22" lighting-color="#fff4cc" result="s"><feDistantLight azimuth="235" elevation="38"/></feSpecularLighting>
<feComposite in="s" in2="SourceAlpha" operator="in" result="s2"/><feComposite in="SourceGraphic" in2="s2" operator="arithmetic" k1="0" k2="1" k3=".75" k4="0" result="lit"/>
<feDropShadow dx="1.2" dy="2" stdDeviation="1.6" flood-color="#3a0000" flood-opacity=".55"/></filter>
<clipPath id="ic"><circle r="86"/></clipPath><path id="rt" d="M-62 26 Q0 58 62 26"/></defs>
<g filter="url(#emb)">
<path d="{gear}" fill="url(#gold)" stroke="#7a4b00" stroke-width="1.2"/>
<circle r="88" fill="none" stroke="#9a6400" stroke-width="2.4"/><circle r="85" fill="none" stroke="#ffe9a0" stroke-width=".8" opacity=".8"/>
<g clip-path="url(#ic)" stroke="#fff3b0" stroke-width="1.8" opacity=".6">{rays}</g>
<path d="M-36 80 A36 36 0 0 1 36 80 Z" fill="url(#gold)" stroke="#a06a00" stroke-width="1.5"/>
<line x1="-74" y1="-122" x2="-14" y2="-2" stroke="url(#gold)" stroke-width="5.5" stroke-linecap="round"/>
<path d="M-81 -137 L-69 -115 L-77 -111 Z" fill="url(#gold)" stroke="#8e5a00" stroke-width="1"/>
<path d="{flag}" fill="url(#red)" stroke="url(#gold)" stroke-width="3" stroke-linejoin="round"/>
<path d="M28 -96 C48 -70 52 -44 60 -22" fill="none" stroke="#ff8a7a" stroke-width="7" opacity=".28"/>
<circle cx="-30" cy="-80" r="19" fill="url(#gold)" stroke="#8e5a00" stroke-width="1.4"/><path d="{star}Z" fill="#d6000c"/>
<path d="M-74 10 Q0 44 74 10 L76 38 Q0 72 -76 38 Z" fill="url(#red)" stroke="url(#gold)" stroke-width="3" stroke-linejoin="round"/>
<text font-family="STXingkai,华文行楷,KaiTi" font-size="19" fill="#ffe27a" text-anchor="middle" letter-spacing="2"><textPath href="#rt" startOffset="50%">中国共青团</textPath></text>
</g></svg>'''

# =============================================================== 华丽扇轮（中心盘 + 外环，不再有遮挡照片的扇骨）
def wheel_svg():
    sz = 2 * RO * 2                                       # 2 倍分辨率
    beads = ''.join(f'<circle cx="{466 * math.cos(math.radians(a)):.1f}" cy="{466 * math.sin(math.radians(a)):.1f}" r="5"/>' for a in range(0, 360, 4))
    ticks = ''.join(f'<line x1="{390 * math.cos(math.radians(a)):.1f}" y1="{390 * math.sin(math.radians(a)):.1f}" x2="{440 * math.cos(math.radians(a)):.1f}" y2="{440 * math.sin(math.radians(a)):.1f}"/>' for a in range(0, 360, 3))
    rays = ''.join(f'<line x1="0" y1="0" x2="{290 * math.cos(math.radians(a)):.1f}" y2="{290 * math.sin(math.radians(a)):.1f}"/>' for a in range(0, 360, 10))
    # 外环金珠与菱形标记、中心盘花瓣：都不进入照片区域，但旋转时清晰可见
    obeads = ''.join(f'<circle cx="{(RO - 17) * math.cos(math.radians(a)):.1f}" cy="{(RO - 17) * math.sin(math.radians(a)):.1f}" r="4.2"/>' for a in range(0, 360, 4) if a % 30)
    marks = ''.join(f'<path transform="rotate({a}) translate({RO - 17} 0)" d="M-15 0 L0 -9 L15 0 L0 9 Z"/>' for a in range(0, 360, 30))
    petals = ''.join(f'<path transform="rotate({a})" d="M150 0 C190 -46 250 -40 285 0 C250 40 190 46 150 0 Z M175 0 L262 0"/>' for a in range(15, 360, 60))
    return f'''<svg width="{sz}" height="{sz}" viewBox="{-RO} {-RO} {2 * RO} {2 * RO}" xmlns="http://www.w3.org/2000/svg"><defs>
<radialGradient id="hub" cx="45%" cy="45%" r="60%"><stop offset="0" stop-color="#ef3b33"/><stop offset=".55" stop-color="#c3121b"/><stop offset="1" stop-color="#6c050a"/></radialGradient>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff2b8"/><stop offset=".3" stop-color="#d9a238"/><stop offset=".55" stop-color="#ffe598"/><stop offset=".8" stop-color="#a86c12"/><stop offset="1" stop-color="#f1cd72"/></linearGradient>
<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a4a0a"/><stop offset=".3" stop-color="#f7dc8c"/><stop offset=".5" stop-color="#fff4cc"/><stop offset=".7" stop-color="#d49a32"/><stop offset="1" stop-color="#6e4106"/></linearGradient>
<filter id="sh"><feDropShadow dx="0" dy="0" stdDeviation="10" flood-color="#2a0000" flood-opacity=".6"/></filter></defs>
<circle r="{RO - 4}" fill="none" stroke="url(#gold)" stroke-width="8" filter="url(#sh)"/>
<circle r="{RO - 30}" fill="none" stroke="url(#gold)" stroke-width="2.5" opacity=".9"/>
<g fill="#f6cf6a">{obeads}</g><g fill="url(#gold)" stroke="#7a4a0a" stroke-width="1.5">{marks}</g>
<circle r="{RI}" fill="url(#hub)" filter="url(#sh)"/>
<circle r="{RI - 8}" fill="none" stroke="url(#gold)" stroke-width="12"/><circle r="{RI - 26}" fill="none" stroke="url(#gold)" stroke-width="3"/>
<g fill="#f2c45a">{beads}</g>
<g stroke="#f0c25a" stroke-width="3" opacity=".55">{ticks}</g>
<circle r="372" fill="none" stroke="url(#gold)" stroke-width="4"/><circle r="300" fill="none" stroke="url(#gold)" stroke-width="2.5"/>
<g stroke="#ffd36a" stroke-width="2" opacity=".25">{rays}</g>
<g fill="none" stroke="url(#gold)" stroke-width="4" opacity=".85">{petals}</g></svg>'''

# =============================================================== 封面装饰轮
def deco_svg():
    t = ''.join(f'<line x1="{820 * math.cos(math.radians(a)):.1f}" y1="{820 * math.sin(math.radians(a)):.1f}" x2="{(880 if a % 10 else 905) * math.cos(math.radians(a)):.1f}" y2="{(880 if a % 10 else 905) * math.sin(math.radians(a)):.1f}"/>' for a in range(0, 360, 2))
    petals = ''.join(f'<path transform="rotate({k * 15})" d="M0 -560 Q60 -660 0 -760 Q-60 -660 0 -560 Z"/>' for k in range(24))
    return f'''<svg width="2000" height="2000" viewBox="-1000 -1000 2000 2000" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff0b0"/><stop offset=".5" stop-color="#d9a441"/><stop offset="1" stop-color="#f6d98a"/></linearGradient></defs>
<g fill="none" stroke="url(#g)" opacity=".55"><circle r="960" stroke-width="5"/><circle r="935" stroke-width="2"/><circle r="800" stroke-width="3"/>
<circle r="540" stroke-width="2"/><circle r="520" stroke-width="5"/></g>
<g stroke="url(#g)" stroke-width="3" opacity=".45">{t}</g><g fill="none" stroke="url(#g)" stroke-width="3" opacity=".5">{petals}</g></svg>'''

# =============================================================== 印章
def seal_svg(txt='青春'):
    return f'''<svg width="420" height="420" viewBox="0 0 420 420" xmlns="http://www.w3.org/2000/svg"><defs>
<filter id="r"><feTurbulence type="fractalNoise" baseFrequency=".06" numOctaves="3" seed="3"/><feDisplacementMap in="SourceGraphic" scale="9"/></filter>
<filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="5" result="t"/>
<feColorMatrix in="t" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -2.2 1.35"/><feComposite in="SourceGraphic" operator="in"/></filter></defs>
<g><g filter="url(#r)"><rect x="20" y="20" width="380" height="380" rx="26" fill="#c8101b"/>
<text x="210" y="196" font-family="STLiti,隶书,SimLi" font-size="170" fill="#fff4e6" text-anchor="middle">{txt[0]}</text>
<text x="210" y="372" font-family="STLiti,隶书,SimLi" font-size="170" fill="#fff4e6" text-anchor="middle">{txt[1]}</text></g></g></svg>'''

# =============================================================== 照片处理
def fit169(img, cx=.5, cy=.5, zoom=1.0):
    h, w = img.shape[:2]
    cw = min(w, h * 16 / 9) / zoom; ch = cw * 9 / 16
    x0 = int(np.clip(cx * w - cw / 2, 0, w - cw)); y0 = int(np.clip(cy * h - ch / 2, 0, h - ch))
    return cv2.resize(img[y0:y0 + int(ch), x0:x0 + int(cw)], (W, H), interpolation=cv2.INTER_LANCZOS4)

def grade(img, sat=1.12, con=1.08, warm=6, bright=0):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255); im = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    im = (im - 128) * con + 128 + bright
    im[..., 2] += warm; im[..., 0] -= warm * .6
    bl = cv2.GaussianBlur(im, (0, 0), 2.2); im = im * 1.35 - bl * .35        # 轻度锐化
    return np.clip(im, 0, 255).astype(np.uint8)

def duotone(img, stops=('#250003', '#8a0a12', '#e0342c', '#ffd27a'), gamma=1.0):
    L = (cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255) ** gamma
    cs = [hexbgr(c) for c in stops]; n = len(cs) - 1
    t = np.clip(L * n, 0, n - 1e-4); i = t.astype(int); f = (t - i)[..., None]
    lut = np.stack(cs)
    return (lut[i] * (1 - f) + lut[i + 1] * f).astype(np.uint8)

def red_wash(img, a=.45, dark=.35, side='left'):
    """压暗并染红，给文字留出空间。"""
    im = img.astype(np.float32) * (1 - dark)
    t = (xx / W) if side == 'left' else (1 - xx / W)
    m = np.clip(1.15 - t * 1.1, .35, 1)[..., None] * a
    return np.clip(im * (1 - m) + hexbgr('#9a0610') * m, 0, 255).astype(np.uint8)

def sky_to_red(img):
    """把灰白天空换成由深红到金色的晚霞。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    raw = ((hsv[..., 2] > 140) & (hsv[..., 1] < 80)).astype(np.uint8)
    closed = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))   # 跨过旗杆连通
    n, lab = cv2.connectedComponents(closed)
    top = set(np.unique(lab[:6])) - {0}
    sky = (np.isin(lab, list(top)) & (raw > 0)).astype(np.float32)
    sky = cv2.GaussianBlur(sky, (0, 0), 3)[..., None]
    t = (yy / (H * .75))[..., None].clip(0, 1)
    grad = hexbgr('#5a020a') * (1 - t) + hexbgr('#f2a04a') * t
    grad = grad * (.85 + .3 * hsv[..., 2:3] / 255)
    return np.clip(img * (1 - sky) + grad * sky, 0, 255).astype(np.uint8)

def ring_canvas(img, theta):
    """1600x900 设计稿对应的扇面贴图（2 倍）：画面放进以扇面圆心为中心的方形画布，外圈镜像模糊补齐，再预旋转。"""
    k = 2.0; Sz = int(2 * RO * k)
    im = cv2.resize(img, (int(1600 * k), int(900 * k)), interpolation=cv2.INTER_AREA)
    top = int((RO - PY) * k); left = int((RO - PX) * k)
    pad = np.pad(im, ((top, Sz - top - im.shape[0]), (left, 0), (0, 0)), mode='symmetric')[:, :Sz]
    mask = np.zeros(pad.shape[:2], np.float32); mask[top:top + im.shape[0], left:] = 1
    mask = cv2.GaussianBlur(mask, (0, 0), 10)[..., None]
    out = (pad * mask + cv2.GaussianBlur(pad, (0, 0), 22) * (1 - mask)).astype(np.uint8)
    M = cv2.getRotationMatrix2D((Sz / 2, Sz / 2), theta, 1.0)
    return cv2.warpAffine(out, M, (Sz, Sz), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# =============================================================== 团徽"光晕"版与金色闪光（飞入、穿越时叠在团徽上，随 Morph 淡出）
def emblem_glow():
    em = cv2.imdecode(np.fromfile(os.path.join(A, 'emblem.png'), np.uint8), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    em = cv2.resize(em, (1000, 1000), interpolation=cv2.INTER_AREA)
    a = em[..., 3]; rgb = em[..., :3] * a[..., None]
    b = lambda x, s: cv2.GaussianBlur(x, (0, 0), s)
    ab = b(a, 9); cb = b(rgb, 9) / np.maximum(ab[..., None], 1e-3)
    n = 1000; yy2, xx2 = np.mgrid[0:n, 0:n].astype(np.float32) / n
    pearl = np.stack([.93 + .07 * np.sin(xx2 * 6 + yy2 * 3), .86 + .1 * np.sin(xx2 * 5 - 1), .97 * np.ones_like(xx2)], -1)  # BGR 珠光
    t = np.clip(.35 + .5 * np.exp(-((xx2 - yy2 + .1) / .28) ** 2), 0, 1)[..., None]
    core = cb * (1 - t) + pearl * t
    halo = b(a, 45) * .85
    gold = np.array([.35, .78, 1.0])
    out_a = np.clip(np.maximum(np.clip(ab * 1.15, 0, 1), halo), 0, 1)
    w = np.clip(ab * 1.15, 0, 1)[..., None]
    col = (core * w + gold * halo[..., None] * (1 - w)) / np.maximum((w + halo[..., None] * (1 - w)), 1e-3)
    save('emblem_glow.png', (np.dstack([np.clip(col, 0, 1), out_a]) * 255).astype(np.uint8))

def flash():
    n_w, n_h = 1920, 1080
    y2, x2 = np.mgrid[0:n_h, 0:n_w].astype(np.float32)
    d = np.sqrt(((x2 - n_w / 2) / (n_w * .55)) ** 2 + ((y2 - n_h / 2) / (n_h * .6)) ** 2)
    t = np.clip(d, 0, 1)[..., None]
    col = np.array([235, 250, 255], np.float32) * (1 - t) + np.array([60, 170, 250], np.float32) * t
    alpha = np.clip(1 - .12 * d, .85, 1)
    save('flash.png', np.dstack([col, alpha * 255]).astype(np.uint8))

if __name__ == '__main__' and '--glow' in os.sys.argv:
    emblem_glow(); flash(); raise SystemExit('glow ok')

if __name__ == '__main__' and '--wheel' in os.sys.argv:
    svg_png('wheel.png', wheel_svg(), 4 * RO, 4 * RO); raise SystemExit('wheel ok')

if __name__ == '__main__':
    # 矢量装饰
    svg_png('rays.png', rays_svg().replace('width="4000" height="4000"','width="2400" height="2400" viewBox="0 0 4000 4000"'), 2400, 2400)
    svg_png('cloud.png', cloud_svg(1.0), 1500, 900)
    svg_png('frame.png', frame_svg(), W, H)
    svg_png('emblem.png', emblem_svg(), 2000, 2000)
    emblem_glow(); flash()
    svg_png('wheel.png', wheel_svg(), 4 * RO, 4 * RO)
    svg_png('deco.png', deco_svg(), 2000, 2000)
    svg_png('seal.png', seal_svg(), 420, 420)
    # 背景
    cover = silk(seed=1); cover = add_glow(cover, W / 2, H * .3, W * .32, H * .38, '#ff9a3a', .28)
    save('cover_bg.jpg', cover)
    city = duotone(grade(fit169(read(os.path.join(HD, 'night.jpg')), cy=.62, zoom=1.0), con=1.15), gamma=.85)
    alpha = np.clip((yy / H - .40) / .38, 0, 1) ** 1.4
    save('cover_city.png', np.dstack([city, (alpha * 235).astype(np.uint8)]))
    emb = silk('#c81822', '#7e0710', '#1c0003', seed=2, cy=.4); save('emb_bg.jpg', add_glow(emb, W / 2, H * .38, W * .3, H * .42, '#ff7a2a', .22))
    # 照片（扇面页）
    photos = {
        'night': grade(fit169(read(os.path.join(HD, 'night.jpg')), cy=.6), sat=1.15, con=1.1),
        'huabiao': grade(fit169(read(os.path.join(HD, 'huabiao.jpg')), cx=.5, cy=.33), sat=1.1, warm=8),
        'gateflags': grade(fit169(read(os.path.join(HD, 'gate_flags.jpg')), cx=.55, cy=.52), sat=1.12, warm=6),
        'history': red_wash(duotone(grade(fit169(read(os.path.join(HD, 'monument.jpg')), cx=.42, cy=.4)), ('#14000a', '#5e0610', '#b81c26', '#ffcf80'), .9),
                            a=.55, dark=.35, side='right'),
        'oath': add_glow(silk('#c01620', '#76060f', '#180003', seed=5, cx=.68, cy=.45), W * .66, H * .45, W * .3, H * .4, '#ff8a30', .18),
        'hongqi': red_wash(grade(fit169(read(os.path.join(HD, 'gate_lantern.jpg')), cy=.55), sat=1.15), a=.55, dark=.42, side='right'),
        'youth': red_wash(grade(fit169(read(os.path.join(HD, 'trails.jpg')), cy=.5), sat=1.1), a=.5, dark=.38, side='right'),
        'party': grade(sky_to_red(grade(fit169(read(os.path.join(HD, 'greathall.jpg')), cx=.62, cy=.42, zoom=1.15), con=1.12)), sat=1.12, warm=4),
    }
    for k, im in photos.items():
        save(f'photo_{k}.jpg', im)
        save(f'ring_{k}.jpg', ring_canvas(im, FAN_THETA[k]), 90)
    import optimize_assets; optimize_assets.run()
    print('assets ok')
