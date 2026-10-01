# -*- coding: utf-8 -*-
"""用 PowerPoint(COM) 生成《团日活动》PPT：Morph 平滑切换、纸飞机转场、旋转扇面、金色浮雕文字与进入动画。
坐标按 1600x900 设计稿书写，自动换算为 960x540 磅。素材由 make_assets.py 生成。"""
import os, sys, math, random, time
from win32com.client import gencache, constants as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, '_build', 'assets')
NOLOOP = '--video' in sys.argv
OUT = os.path.join(ROOT, '团日活动_红色精神.pptx') if not NOLOOP else os.path.join(os.environ['TEMP'], 'tuanri_preview.pptx')

K = 0.6
PX, PY, RO, RI = -434, 450, 904, 509
BRUSH, SANS, SONG = '华文行楷', '微软雅黑', '华文中宋'

def pt(v): return v * K
def RGB(r, g, b): return r + g * 256 + b * 65536
def asset(n): return os.path.join(A, n)

gencache.EnsureModule('{2DF8D04C-5BFA-101B-BDE5-00AA0044DE52}', 0, 2, 8)
app = gencache.EnsureDispatch('PowerPoint.Application')
pres = app.Presentations.Add(WithWindow=False)
pres.PageSetup.SlideWidth, pres.PageSetup.SlideHeight = 960, 540
pres.SlideShowSettings.ShowMediaControls = False          # 放映时不显示视频播放条

# ================================================================== 基础
def pic(s, f, x, y, w, h, name, rot=0):
    sh = s.Shapes.AddPicture(asset(f), False, True, pt(x), pt(y), pt(w), pt(h))
    sh.Name = name; sh.Rotation = rot % 360
    return sh

def picc(s, f, cx, cy, w, h, name, rot=0):           # 以中心定位
    return pic(s, f, cx - w / 2, cy - h / 2, w, h, name, rot)

def fill(sh, rgb, t=0.0):
    sh.Fill.Visible = True; sh.Fill.Solid(); sh.Fill.ForeColor.RGB = RGB(*rgb); sh.Fill.Transparency = t

def gradfill(f, stops, style):
    """f: FillFormat；stops: [(位置, rgb, 透明度), ...]"""
    f.Visible = True
    f.TwoColorGradient(style, 1)
    gs = f.GradientStops
    gs.Item(1).Color.RGB = RGB(*stops[0][1]); gs.Item(1).Position = stops[0][0]; gs.Item(1).Transparency = stops[0][2]
    gs.Item(2).Color.RGB = RGB(*stops[-1][1]); gs.Item(2).Position = stops[-1][0]; gs.Item(2).Transparency = stops[-1][2]
    for i, (p, c, t) in enumerate(stops[1:-1]):
        gs.Insert(RGB(*c), p, t, i + 2)

def noline(sh): sh.Line.Visible = False

def rect(s, x, y, w, h, name, shape=None):
    sh = s.Shapes.AddShape(shape or C.msoShapeRectangle, pt(x), pt(y), pt(w), pt(h)); sh.Name = name; return sh

def oval(s, cx, cy, r, name):
    sh = s.Shapes.AddShape(C.msoShapeOval, pt(cx - r), pt(cy - r), pt(2 * r), pt(2 * r)); sh.Name = name; return sh

def poly(s, pts, name):
    fb = s.Shapes.BuildFreeform(C.msoEditingAuto, pt(pts[0][0]), pt(pts[0][1]))
    for x, y in pts[1:] + [pts[0]]:
        fb.AddNodes(C.msoSegmentLine, C.msoEditingAuto, pt(x), pt(y))
    sh = fb.ConvertToShape(); sh.Name = name; return sh

def line(s, x0, y0, x1, y1, name, rgb=(226, 182, 92), w=1.2, t=0):
    l = s.Shapes.AddLine(pt(x0), pt(y0), pt(x1), pt(y1)); l.Name = name
    l.Line.ForeColor.RGB = RGB(*rgb); l.Line.Weight = w; l.Line.Transparency = t; return l

GOLD = [(0, (255, 248, 206), 0), (.28, (248, 216, 118), 0), (.5, (199, 142, 42), 0), (.7, (252, 230, 156), 0), (1, (166, 108, 24), 0)]
CREAM = (250, 230, 190)

def text(s, txt, x, y, w, h, name, size, font=BRUSH, rgb=(255, 255, 255), gold=False, bold=False,
         spacing=0, align='c', t=0.0, vertical=False, shadow=True, bevel=None, top=False, line_sp=None):
    sh = s.Shapes.AddTextbox(C.msoTextOrientationHorizontal, pt(x), pt(y), pt(w), pt(h)); sh.Name = name
    tf = sh.TextFrame2; tf.WordWrap = True; tf.AutoSize = C.msoAutoSizeNone
    tf.MarginLeft = tf.MarginRight = tf.MarginTop = tf.MarginBottom = 0
    tf.VerticalAnchor = C.msoAnchorTop if top else C.msoAnchorMiddle
    if vertical: tf.Orientation = C.msoTextOrientationVerticalFarEast
    tr = tf.TextRange; tr.Text = txt
    tr.ParagraphFormat.Alignment = {'c': C.msoAlignCenter, 'l': C.msoAlignLeft, 'r': C.msoAlignRight}[align]
    if line_sp: tr.ParagraphFormat.SpaceWithin = line_sp
    f = tr.Font; f.Name = font; f.NameFarEast = font; f.Size = pt(size); f.Bold = bold; f.Spacing = spacing
    if gold:
        gradfill(f.Fill, GOLD, C.msoGradientHorizontal)
        b = bevel if bevel is not None else max(1.0, pt(size) / 40)
        if b:
            td = sh.TextFrame2.ThreeD
            td.BevelTopType = C.msoBevelCircle; td.BevelTopInset = b; td.BevelTopDepth = b * .6
    else:
        f.Fill.Visible = True; f.Fill.Solid(); f.Fill.ForeColor.RGB = RGB(*rgb); f.Fill.Transparency = t
    if shadow:
        sd = f.Shadow; sd.Visible = True; sd.ForeColor.RGB = RGB(50, 0, 4)
        sd.OffsetX = max(1, pt(size) / 45); sd.OffsetY = max(1.5, pt(size) / 30); sd.Blur = max(3, pt(size) / 14); sd.Transparency = .45
    sh.Left, sh.Top, sh.Width, sh.Height = pt(x), pt(y), pt(w), pt(h)
    return sh

def glow(sh, r, rgb=(255, 196, 60), t=.5):
    sh.Glow.Radius = r; sh.Glow.Color.RGB = RGB(*rgb); sh.Glow.Transparency = t

def plaque(s, cx, cy, w, h, name, txt, size, font=BRUSH, spacing=2):
    """深红渐变匾额 + 双金边 + 金字"""
    o = rect(s, cx - w / 2, cy - h / 2, w, h, name)
    gradfill(o.Fill, [(0, (122, 6, 14), 0), (.5, (196, 22, 30), 0), (1, (122, 6, 14), 0)], C.msoGradientVertical)
    o.Line.ForeColor.RGB = RGB(230, 186, 96); o.Line.Weight = 1.6
    i = rect(s, cx - w / 2 + 7, cy - h / 2 + 7, w - 14, h - 14, name + '_in'); i.Fill.Visible = False
    i.Line.ForeColor.RGB = RGB(230, 186, 96); i.Line.Weight = .6; i.Line.Transparency = .3
    t = text(s, txt, cx - w / 2, cy - h / 2, w, h, name + '_t', size, font=font, gold=True, spacing=spacing, bevel=0, shadow=False)
    return [o, i, t]

def divider(s, cx, y, half, name, gap=0):
    out = [line(s, cx + g * (gap + 14), y, cx + g * half, y, f'{name}_l{g}') for g in (-1, 1)]
    xs = [cx] if gap < 60 else [cx - gap, cx + gap]
    for j, x in enumerate(xs):
        d = rect(s, x - 8, y - 8, 16, 16, f'{name}_d{j}', C.msoShapeDiamond); fill(d, (232, 188, 96)); noline(d); out.append(d)
    return out

# ================================================================== 旋转扇面
def tint_pts():
    return [(PX + math.sqrt(RO ** 2 - (y - PY) ** 2), y) for y in range(-20, 921, 10)] + [(1620, 920), (1620, -20)]

def fan(s, theta, ring, shift=0, tint=(.40, .82)):
    """tint: (靠近扇面处透明度, 右侧透明度)"""
    cx = PX + shift
    tn = poly(s, tint_pts(), '!!tint'); noline(tn)
    gradfill(tn.Fill, [(0, (70, 0, 6), tint[0]), (.45, (110, 4, 12), (tint[0] + tint[1]) / 2), (1, (120, 6, 14), tint[1])], C.msoGradientVertical)
    r = s.Shapes.AddShape(C.msoShapeDonut, pt(cx - RO), pt(PY - RO), pt(2 * RO), pt(2 * RO)); r.Name = '!!ring'
    r.Adjustments.SetItem(1, (RO - RI) / (2 * RO))
    r.Fill.UserPicture(asset(ring)); r.Fill.RotateWithObject = True; noline(r); r.Rotation = theta % 360
    w = picc(s, 'wheel.png', cx, PY, 2 * RO, 2 * RO, '!!wheel', theta)
    return dict(tint=tn, ring=r, wheel=w)

# ================================================================== 金色光点
def particles(s, seed, area=(0, 0, 1600, 900), n=16):
    rnd = random.Random(seed); out = []
    for i in range(n):
        r = 2.5 + (i * 7) % 6 * .9 + rnd.random() * 1.5
        x, y = rnd.uniform(area[0], area[2]), rnd.uniform(area[1], area[3]); tr = rnd.uniform(.05, .45)
        # 预烘焙的发光金点图片（比 PPT 实时"发光"效果轻得多，切换时不卡）
        w = r / .15
        out.append(picc(s, f'dot{0 if tr < .17 else 1 if tr < .31 else 2}.png', x, y, w, w, f'!!pt{i}'))
    return out

# ================================================================== 动画 / 切换
def trans(s, effect, dur, auto=False):
    t = s.SlideShowTransition
    t.EntryEffect = effect; t.Duration = dur; t.AdvanceOnClick = True; t.AdvanceOnTime = auto
    if auto: t.AdvanceTime = 0

MORPH = C.ppEffectMorphByObject

def new_slide():
    s = pres.Slides.Add(pres.Slides.Count + 1, C.ppLayoutBlank)
    s.FollowMasterBackground = False
    s.Background.Fill.Solid(); s.Background.Fill.ForeColor.RGB = RGB(70, 2, 8)
    return s

def emblem(s, cx, cy, h, rot=0, g=True):
    if g:   # 带烘焙外发光的版本：团徽占画布 80%，所以整体放大 1.25 倍
        sh = picc(s, 'emblem_halo.png', cx, cy, h * 1.25, h * 1.25, '!!emb', rot)
    else:
        sh = picc(s, 'emblem.png', cx, cy, h, h, '!!emb', rot)
    return sh

def three_d(sh, rx, ry, rz=0):
    sh.ThreeD.SetPresetCamera(C.msoCameraPerspectiveFront)
    sh.ThreeD.RotationX = rx % 360; sh.ThreeD.RotationY = ry % 360; sh.ThreeD.RotationZ = rz % 360

def clouds(s, specs, prefix):
    out = []
    for i, (cx, cy, w, flip) in enumerate(specs):
        c = picc(s, 'cloud.png', cx, cy, w, w * .6, f'{prefix}{i}')
        if flip: c.Flip(C.msoFlipHorizontal)
        out.append(c)
    return out

# ================================================================== 0~1 封面（放映开始时自动"组装"成形）
BG_NAMES = ('!!base', '!!embbg', '!!c_bg')
def restack(sl):
    """统一层次：光点紧贴背景之上，在所有图形与文字之下。"""
    shapes = [sl.Shapes(i) for i in range(1, sl.Shapes.Count + 1)]
    for sh in shapes:
        if sh.Name.startswith('!!pt'): sh.ZOrder(C.msoSendToBack)
    for sh in shapes:
        if sh.Name in BG_NAMES: sh.ZOrder(C.msoSendToBack)

def cover(upto=5):
    """正式封面。upto<5 时只放前几组元素，用来导出开场动画的分阶段画面。"""
    s = new_slide()
    pic(s, 'cover_bg.jpg', 0, 0, 1600, 900, '!!c_bg')
    if upto >= 1:
        picc(s, 'rays.png', 800, 230, 1700, 1700, '!!c_rays')
        picc(s, 'deco.png', 800, 330, 1000, 1000, '!!c_deco')
    if upto >= 2:
        pic(s, 'cover_city.png', 0, 90, 1600, 900, '!!c_city')
        clouds(s, [(190, 640, 460, False), (1410, 640, 460, True), (250, 175, 300, False), (1350, 175, 300, True)], '!!c_cloud')
        pic(s, 'frame.png', 0, 0, 1600, 900, '!!c_frame')
        particles(s, 101, (120, 60, 1480, 760))
    if upto >= 3:
        emblem(s, 800, 150, 200)
    if upto >= 4:
        text(s, '团日活动', 250, 250, 1100, 240, '!!c_title', 220, gold=True, spacing=-22)
    if upto >= 5:
        plaque(s, 800, 528, 560, 70, '!!c_plaque', '新时代 · 新青年 · 新担当', 34, font=SONG, spacing=4)
        divider(s, 800, 528, 480, '!!c_div', gap=290)
        text(s, 'COMMUNIST  YOUTH  LEAGUE   ·   THEME  DAY', 300, 585, 1000, 40, '!!c_en', 19, font=SANS, rgb=(240, 200, 120), spacing=4, shadow=False)
        text(s, '主办：XX学院 · XX团支部　　|　　2026年10月', 300, 772, 1000, 46, '!!c_foot', 24, font=SANS, rgb=CREAM, spacing=2)
    restack(s)
    return s

# ---- 开场动画（预渲染视频 render_intro.py）：放映一开始自动播放，结束画面与正式封面完全一致
import render_intro
INTRO_MP4 = os.path.join(A, 'cover_intro.mp4')
stage_png = [os.path.join(A, f'cover_stage{k}.png') for k in range(6)]
for k in range(6):
    tmp = cover(k); tmp.Export(stage_png[k], 'PNG', 1920, 1080); tmp.Delete()
if not os.path.exists(INTRO_MP4) or '--rerender' in sys.argv or '--intro' in sys.argv:
    print('rendering cover intro video ...', flush=True)
    render_intro.render(stage_png, INTRO_MP4)
s = new_slide()
pic(s, 'cover_bg.jpg', 0, 0, 1600, 900, '!!c_bg')
iv = s.Shapes.AddMediaObject2(INTRO_MP4, False, True, 0, 0, 960, 540); iv.Name = 'intro_video'
iv.MediaFormat.SetDisplayPicture(0)
ips = iv.AnimationSettings.PlaySettings
ips.PlayOnEntry = True; ips.HideWhileNotPlaying = False; ips.RewindMovie = False
iseq = s.TimeLine.MainSequence
for i in range(1, iseq.Count + 1): iseq.Item(i).Timing.TriggerType = C.msoAnimTriggerWithPrevious
trans(s, C.ppEffectFadeSmoothly, .6, auto=True)
s = cover(5)
s.SlideShowTransition.EntryEffect = C.ppEffectNone          # 视频最后一帧即封面，直接切换无痕
s.SlideShowTransition.AdvanceOnClick = True; s.SlideShowTransition.AdvanceOnTime = False

# ================================================================== 2~4 团徽飞入（自动连播）
def emb_slide(rays_at=(800, 330)):
    s = new_slide(); pic(s, 'emb_bg.jpg', 0, 0, 1600, 900, '!!embbg')
    picc(s, 'rays.png', *rays_at, 1500, 1500, '!!rays'); return s

def glow_emblem(s, cx, cy, h, rx=0, ry=0, rot=0):
    """清晰团徽 + 叠在上面的珠光光晕版（同一变换）。光晕在最后一帧去掉，Morph 时自然淡出。"""
    e = emblem(s, cx, cy, h, rot, g=False); g = picc(s, 'emblem_glow.png', cx, cy, h, h, '!!embglow', rot)
    for sh in (e, g):
        if rx or ry: three_d(sh, rx, ry)
    return e, g

# 团徽 3D 飞入改为预渲染视频（render_fly.py），放映时不再逐页计算 3D/光晕，非常流畅。
# 视频下面垫一层"落定画面"，视频最后一帧与它一致，再 Morph 到口号页即可无缝衔接。
import render_fly
s = new_slide(); pic(s, 'emb_bg.jpg', 0, 0, 1600, 900, '!!embbg')
picc(s, 'rays.png', 800, 330, 1500, 1500, '!!rays')
emblem(s, 800, 320, 310)
FLY_END = os.path.join(A, 'fly_end.png'); FLY_MP4 = os.path.join(A, 'emblem_fly.mp4')
s.Export(FLY_END, 'PNG', 1920, 1080)
if not os.path.exists(FLY_MP4) or '--rerender' in sys.argv or '--fly' in sys.argv:
    print('rendering emblem fly-in video ...', flush=True)
    render_fly.render(FLY_END, FLY_MP4)
vid = s.Shapes.AddMediaObject2(FLY_MP4, False, True, 0, 0, 960, 540); vid.Name = 'fly_video'
vid.MediaFormat.SetDisplayPicture(0)                      # 封面纸飞机转场时露出的是视频第一帧
ps = vid.AnimationSettings.PlaySettings
ps.PlayOnEntry = True; ps.HideWhileNotPlaying = False; ps.RewindMovie = False
seq = s.TimeLine.MainSequence
for i in range(1, seq.Count + 1):                          # 进入本页即自动播放，不等单击
    seq.Item(i).Timing.TriggerType = C.msoAnimTriggerWithPrevious
trans(s, C.ppEffectAirplaneLeft, 2.0, auto=True)

s = emb_slide()
picc(s, 'deco.png', 800, 320, 820, 820, '!!deco')
emblem(s, 800, 320, 310)
text(s, '新时代　新青年　新担当', 200, 560, 1200, 90, 'slogan', 60, font=SONG, gold=True, bold=True, spacing=6)
text(s, 'NEW  ERA  ·  NEW  YOUTH  ·  NEW  MISSION', 300, 650, 1000, 40, 'slogan_en', 18, font=SANS, rgb=(240, 200, 120), spacing=4, shadow=False)
divider(s, 800, 712, 300, 'emb_div', gap=40)
clouds(s, [(170, 770, 380, False), (1430, 770, 380, True)], '!!cloud')
particles(s, 404)
trans(s, MORPH, 1.0)

# ================================================================== 5 活动流程（团徽移到左侧，右侧议程卡片依次就位）
AGENDA = [('01', '回顾光辉团史', '追寻百年青春足迹'),
          ('02', '重温入团誓词', '不忘初心 · 牢记使命'),
          ('03', '青年使命担当', '青春逢盛世 · 奋斗正当时'),
          ('04', '交流分享 · 总结', '畅谈收获 · 凝聚力量')]
s = emb_slide(rays_at=(400, 380))
picc(s, 'deco.png', 400, 380, 640, 640, '!!deco')
emblem(s, 400, 360, 250)
text(s, '活动流程', 100, 560, 600, 140, 'ag_title', 104, gold=True, spacing=-8)
text(s, 'A G E N D A', 100, 690, 600, 40, 'ag_en', 20, font=SANS, rgb=(240, 200, 120), shadow=False)
line(s, 770, 150, 770, 750, 'ag_vline', t=.25)
for i, (no, tt, sub) in enumerate(AGENDA):
    y = 160 + i * 150
    card = rect(s, 820, y, 700, 120, f'ag_card{i}', C.msoShapeRoundedRectangle); card.Adjustments.SetItem(1, .08)
    gradfill(card.Fill, [(0, (150, 12, 22), .25), (1, (90, 4, 12), .55)], C.msoGradientVertical)
    card.Line.ForeColor.RGB = RGB(230, 186, 96); card.Line.Weight = 1; card.Line.Transparency = .35
    text(s, no, 840, y + 10, 140, 100, f'ag_no{i}', 72, font=SONG, gold=True, bold=True, bevel=0)
    line(s, 990, y + 28, 990, y + 92, f'ag_sep{i}', t=.3)
    text(s, tt, 1020, y + 16, 480, 56, f'ag_t{i}', 40, font=SONG, rgb=(255, 236, 196), bold=True, align='l')
    text(s, sub, 1020, y + 70, 480, 36, f'ag_s{i}', 22, font=SONG, rgb=(236, 190, 130), align='l', shadow=False)
    o = oval(s, 770, y + 60, 9, f'ag_dot{i}'); fill(o, (240, 200, 110)); noline(o)
clouds(s, [(1440, 820, 300, True)], '!!cloud')
particles(s, 455)
trans(s, MORPH, 1.6)

# ================================================================== 6~7 穿过团徽 → 天安门夜景旋转展开
s = emb_slide()
picc(s, 'photo_night.jpg', 800, 450, 1600 * 1.18, 900 * 1.18, '!!base')
fan(s, 0, 'ring_night.jpg', shift=-1900, tint=(1, 1))
glow_emblem(s, 800, 450, 2600)
pic(s, 'flash.png', 0, 0, 1600, 900, '!!flash')
particles(s, 505)
trans(s, MORPH, 1.0, auto=True)

def caption(s, big, small, seed):
    pn = rect(s, 1040, 0, 560, 900, '!!panel'); noline(pn)
    gradfill(pn.Fill, [(0, (60, 0, 6), 1), (.55, (60, 0, 6), .55), (1, (40, 0, 4), .25)], C.msoGradientVertical)
    line(s, 1392, 120, 1392, 780, f'cap_line{seed}', w=1, t=.2)
    text(s, big, 1410, 110, 170, 680, f'cap_big{seed}', 118, gold=True, vertical=True, spacing=4)
    text(s, small, 1300, 150, 80, 600, f'cap_small{seed}', 30, font=SONG, rgb=CREAM, vertical=True, spacing=6)
    picc(s, 'seal.png', 1340, 800, 66, 66, f'cap_seal{seed}')

def fan_slide(key, theta, seed, tint=(.40, .82), dur=1.6, cap=None):
    s = new_slide()
    pic(s, f'photo_{key}.jpg', 0, 0, 1600, 900, '!!base')
    fan(s, theta, f'ring_{key}.jpg', tint=tint)
    particles(s, seed)
    trans(s, MORPH, dur)
    if cap: caption(s, *cap, seed)
    return s

fan_slide('night', 60, 606, tint=(.35, .80), dur=1.8, cap=('不忘初心', '牢记使命 · 砥砺前行'))

# ---------- 8 光辉团史（时间轴）
HISTORY = [('1919', '五四运动爆发\r青年运动起点'),
           ('1922', '中国社会主义\r青年团成立'),
           ('1925', '更名为中国\r共产主义青年团'),
           ('1957', '恢复“中国共产\r主义青年团”名称'),
           ('2022', '建团一百周年\r青春接续奋斗')]
s = fan_slide('history', 100, 656, tint=(.45, .9))
text(s, '光辉团史', 560, 60, 1000, 160, 'hs_title', 130, gold=True, spacing=-10)
text(s, '百年青春足迹 · 一路风华正茂', 560, 215, 1000, 50, 'hs_sub', 28, font=SONG, rgb=CREAM, spacing=4)
ax = line(s, 560, 500, 1560, 500, 'hs_axis', w=1.6, t=.15)
for i, (yr, desc) in enumerate(HISTORY):
    x = 640 + i * 210
    ring = oval(s, x, 500, 20, f'hs_ring{i}'); ring.Fill.Visible = False
    ring.Line.ForeColor.RGB = RGB(236, 192, 100); ring.Line.Weight = 1; ring.Line.Transparency = .3
    o = oval(s, x, 500, 10, f'hs_dot{i}'); fill(o, (250, 214, 120)); noline(o)
    line(s, x, 440, x, 476, f'hs_tick{i}', t=.4)
    text(s, yr, x - 105, 370, 210, 70, f'hs_year{i}', 54, font=SONG, gold=True, bold=True, bevel=0)
    text(s, desc, x - 105, 532, 210, 110, f'hs_desc{i}', 24, font=SONG, rgb=CREAM, top=True, line_sp=1.25)
divider(s, 1060, 720, 380, 'hs_div', gap=20)
text(s, '青年兴则国家兴，青年强则国家强', 560, 745, 1000, 60, 'hs_quote', 34, font=BRUSH, rgb=(250, 220, 150), spacing=2)

fan_slide('huabiao', 140, 707, tint=(.35, .85), cap=('薪火相传', '赓续血脉 · 传承精神'))
fan_slide('gateflags', 180, 808, tint=(.35, .85), cap=('红旗漫卷', '山河锦绣 · 国泰民安'))

# ---------- 11 生在红旗下
s = fan_slide('hongqi', 220, 909, tint=(.45, .9))
clouds(s, [(1420, 130, 300, True), (1300, 800, 380, True)], 'hq_cloud')
text(s, '生在红旗下', 520, 190, 980, 210, 'hq_main1', 168, gold=True, spacing=-18)
text(s, '长在春风里', 640, 400, 960, 210, 'hq_main2', 168, gold=True, spacing=-18)
picc(s, 'seal.png', 1510, 560, 80, 80, 'hq_seal')
divider(s, 1050, 655, 400, 'hq_div', gap=20)
text(s, '目光所至皆为华夏，五星闪耀皆为信仰', 600, 680, 900, 60, 'hq_quote', 34, font=SONG, rgb=CREAM, spacing=3)

# ---------- 12 入团誓词
OATH = ('我志愿加入中国共产主义青年团，坚决拥护中国共产党的领导，遵守团的章程，执行团的决议，'
        '履行团员义务，严守团的纪律，勤奋学习，积极工作，吃苦在前，享受在后，为共产主义事业而奋斗。')
s = fan_slide('oath', 260, 959, tint=(.45, .9))
text(s, '入团誓词', 560, 55, 1000, 170, 'oa_title', 136, gold=True, spacing=-10)
text(s, 'THE  LEAGUE  OATH', 560, 220, 1000, 36, 'oa_en', 18, font=SANS, rgb=(240, 200, 120), spacing=4, shadow=False)
pn = rect(s, 600, 275, 920, 420, 'oa_panel');
gradfill(pn.Fill, [(0, (40, 0, 4), .45), (1, (90, 4, 12), .6)], C.msoGradientVertical)
pn.Line.ForeColor.RGB = RGB(230, 186, 96); pn.Line.Weight = 1.4
inn = rect(s, 612, 287, 896, 396, 'oa_inner'); inn.Fill.Visible = False
inn.Line.ForeColor.RGB = RGB(230, 186, 96); inn.Line.Weight = .6; inn.Line.Transparency = .35
for j, (cx, cy) in enumerate(((600, 275), (1520, 275), (600, 695), (1520, 695))):
    d = rect(s, cx - 10, cy - 10, 20, 20, f'oa_corner{j}', C.msoShapeDiamond); fill(d, (236, 192, 100)); noline(d)
text(s, OATH, 660, 300, 800, 370, 'oa_text', 36, font=SONG, rgb=(255, 238, 205), align='l', spacing=2, line_sp=1.55)
text(s, '—— 摘自《中国共产主义青年团章程》', 900, 712, 620, 40, 'oa_src', 20, font=SANS, rgb=(236, 190, 130), align='r', shadow=False)
picc(s, 'seal.png', 1500, 640, 70, 70, 'oa_seal')
clouds(s, [(1440, 830, 300, True)], 'oa_cloud')

# ---------- 13 中国青年
s = fan_slide('youth', 300, 1010, tint=(.45, .9))
picc(s, 'deco.png', 1060, 330, 760, 760, 'yt_deco')
text(s, '中国青年', 560, 170, 1000, 230, 'yt_title', 190, gold=True, spacing=-20)
text(s, 'C H I N E S E    Y O U T H', 660, 400, 800, 44, 'yt_en', 22, font=SANS, rgb=(240, 200, 120), shadow=False)
divider(s, 1060, 468, 330, 'yt_div', gap=20)
plaque(s, 1060, 545, 640, 92, 'yt_plaque', '青春逢盛世 · 奋斗正当时', 50, spacing=2)
text(s, '新时代的中国青年，生逢其时，重任在肩', 610, 625, 900, 56, 'yt_quote', 28, font=SONG, rgb=CREAM, spacing=3)
clouds(s, [(1430, 790, 360, True)], 'yt_cloud')

# ---------- 14 心中有党
s = fan_slide('party', 340, 1111, tint=(.45, .9))
bt = rect(s, 0, 560, 1600, 340, 'pt_shade'); noline(bt)
gradfill(bt.Fill, [(0, (60, 0, 6), 1), (1, (40, 0, 4), .3)], C.msoGradientHorizontal)
text(s, '心中有党', 560, 50, 1000, 230, 'pt_t1', 200, gold=True, spacing=-14)
text(s, '清澈的爱  ·  只为中国', 760, 285, 600, 50, 'pt_q', 30, font=SONG, rgb=CREAM, spacing=6)
text(s, '成绩理想', 560, 640, 1000, 230, 'pt_t2', 200, gold=True, spacing=-14)
picc(s, 'seal.png', 1525, 330, 70, 70, 'pt_seal')

# ================================================================== 15 结尾（与封面呼应）
s = new_slide()
pic(s, 'cover_bg.jpg', 0, 0, 1600, 900, '!!base')
fan(s, 20, 'ring_party.jpg', shift=-1900, tint=(1, 1))
# 光芒、纹饰轮、祥云、光点、团徽都在预渲染的循环视频里动起来（render_end.py）；文字仍是可编辑对象
import render_end
END_MP4 = os.path.join(A, 'end_loop.mp4')
if not os.path.exists(END_MP4) or '--rerender' in sys.argv:
    print('rendering end loop video ...', flush=True)
    render_end.render(END_MP4)
ev = s.Shapes.AddMediaObject2(END_MP4, False, True, 0, 0, 960, 540); ev.Name = 'end_video'
ev.MediaFormat.SetDisplayPicture(0)
eps = ev.AnimationSettings.PlaySettings
eps.PlayOnEntry = True; eps.LoopUntilStopped = True; eps.HideWhileNotPlaying = False; eps.RewindMovie = True
eseq = s.TimeLine.MainSequence
for i in range(1, eseq.Count + 1): eseq.Item(i).Timing.TriggerType = C.msoAnimTriggerWithPrevious
pic(s, 'frame.png', 0, 0, 1600, 900, 'end_frame')
text(s, '青春向党　奋斗强国', 150, 410, 1300, 170, 'end_title', 130, gold=True, spacing=-6)
plaque(s, 800, 640, 520, 70, 'end_plaque', '感谢聆听 · THANK YOU', 30, font=SONG, spacing=4)
text(s, 'XX学院 · XX团支部　　2026年10月', 300, 735, 1000, 44, 'end_foot', 22, font=SANS, rgb=CREAM, spacing=2)
trans(s, MORPH, 1.8)

for sl in pres.Slides: restack(sl)

# 图片来源写进最后一页备注
cred = open(os.path.join(ROOT, 'images', 'hd', 'credits.txt'), encoding='utf-8').read()
s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = '图片来源（Wikimedia Commons）：\r' + cred.replace('\n', '\r')

# ================================================================== 保存 / 导出预览
if os.path.exists(OUT): os.remove(OUT)
pres.SaveAs(OUT, C.ppSaveAsOpenXMLPresentation)
print('saved', OUT, pres.Slides.Count, 'slides', flush=True)
if NOLOOP:
    vid = sys.argv[sys.argv.index('--video') + 1]
    if os.path.exists(vid): os.remove(vid)
    pres.CreateVideo(vid, True, 2.5, 1080, 25, 90)
    while pres.CreateVideoStatus in (C.ppMediaTaskStatusInProgress, C.ppMediaTaskStatusQueued):
        time.sleep(2)
    print('video status', pres.CreateVideoStatus, flush=True)
pres.Close()
