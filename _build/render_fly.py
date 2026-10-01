# -*- coding: utf-8 -*-
"""预渲染"团徽 3D 飞入"视频（参考用户提供的录屏）：带厚度的金色团徽从左上角侧身飞入，
沿顶部掠过、翻出发光正面，再转正缩小落到中央，光晕褪去。最后几帧淡入到 PPT 导出的落定画面，
因此视频结束时与下一页完全一致。输出 1920x1080 / 30fps H.264。"""
import os, math, shutil, subprocess
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, '_build', 'assets')
VW, VH, FPS = 1920, 1080, 60
SC = VW / 1600                                   # 设计稿 px -> 视频 px
CAM = 2200                                        # 透视相机距离（设计稿 px）

def rd(p, flag=cv2.IMREAD_UNCHANGED):
    return cv2.imdecode(np.fromfile(p, np.uint8), flag)

# 关键帧：(时间s, 中心x, 中心y, 尺寸, 绕X, 绕Y, 平面旋转, 光晕强度)
KEYS = [
    (0.00, -330, -260, 520, 0, 80, 40, .55),     # 从画面左上角外侧飞入，开场画面里没有静止的徽章
    (0.60, 380, 40, 1100, 10, 74, 16, .7),
    (1.20, 900, 50, 1500, 24, 62, -18, .9),
    (1.70, 1150, 320, 1300, 34, 30, -30, 1.0),
    (2.20, 1050, 380, 900, 16, 38, -16, 1.0),
    (2.70, 860, 340, 520, 5, 14, -5, .55),
    (3.20, 800, 320, 310, 0, 0, 0, 0.0),
]
RAYS = [(0.0, 260), (1.2, 800), (2.2, 1250), (3.2, 1500)]
T_END, T_FADE, T_HOLD = 3.2, .35, .2

def catmull(keys, t, idx):
    ts = [k[0] for k in keys]
    if t <= ts[0]: return keys[0][idx]
    if t >= ts[-1]: return keys[-1][idx]
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    p = [keys[max(i - 1, 0)][idx], keys[i][idx], keys[i + 1][idx], keys[min(i + 2, len(keys) - 1)][idx]]
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    return .5 * ((2 * p[1]) + (-p[0] + p[2]) * u + (2 * p[0] - 5 * p[1] + 4 * p[2] - p[3]) * u * u + (-p[0] + 3 * p[1] - 3 * p[2] + p[3]) * u ** 3)

def raw_state(t):
    k = [catmull(KEYS, t, i) for i in range(1, 8)]
    # 尺寸用对数插值更自然
    lh = catmull([(kk[0], math.log(kk[3])) for kk in KEYS], t, 1)
    k[2] = math.exp(lh)
    k[6] = float(np.clip(k[6], 0, 1))
    return k

# 按"运动量"重新分配时间：整段匀顺地快进、缓缓落定，避免关键帧之间忽快忽慢
_ts = np.linspace(0, KEYS[-1][0], 2000)
_st = np.array([raw_state(t) for t in _ts])
_d = np.abs(np.diff(_st[:, 0])) + np.abs(np.diff(_st[:, 1])) + np.abs(np.diff(np.log(_st[:, 2]))) * 600      + (np.abs(np.diff(_st[:, 3])) + np.abs(np.diff(_st[:, 4])) + np.abs(np.diff(_st[:, 5]))) * 8
_cum = np.concatenate([[0], np.cumsum(_d)]); _cum /= _cum[-1]

def state(t):
    x = np.clip(t / KEYS[-1][0], 0, 1)
    prog = 1 - (1 - x) ** 1.6                     # 先快后慢，平稳落定
    return raw_state(float(np.interp(prog, _cum, _ts)))

def rot(rx, ry, rz):
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

class Mip:
    """不同尺寸的源图，变换时选最接近的，避免锯齿与无谓的大图运算。"""
    def __init__(self, img):
        self.levels = {}
        for s in (256, 512, 1024, 2000):
            self.levels[s] = cv2.resize(img, (s, s), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    def get(self, px):
        for s in (256, 512, 1024, 2000):
            if s >= px: return self.levels[s]
        return self.levels[2000]

def warp_into(dst_rgb, dst_a, src, corners, mult=None, opacity=1.0):
    """把方形 RGBA 源图按 4 个目标角点透视贴到画布上（只处理包围盒区域）。"""
    x0, y0 = np.floor(corners.min(0)).astype(int); x1, y1 = np.ceil(corners.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, VW), min(y1, VH)
    if x1 <= x0 or y1 <= y0: return
    n = src.shape[0]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [n, 0], [n, n], [0, n]]), np.float32(corners - [x0, y0]))
    w = cv2.warpPerspective(src, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = w[..., 3:4] * opacity
    rgb = w[..., :3] if mult is None else mult
    dst_rgb[y0:y1, x0:x1] = dst_rgb[y0:y1, x0:x1] * (1 - a) + rgb * a
    dst_a[y0:y1, x0:x1] = dst_a[y0:y1, x0:x1] * (1 - a) + a

def project(cx, cy, h, R, z):
    s = h / 2
    pts = np.array([[-s, -s, z], [s, -s, z], [s, s, z], [-s, s, z]], np.float64) @ R.T
    f = CAM / (CAM + pts[:, 2])
    return np.stack([(cx + pts[:, 0] * f) * SC, (cy + pts[:, 1] * f) * SC], 1)

def draw_emblem(canvas, st, mips):
    cx, cy, h, rx, ry, rz, g = st
    R = rot(rx, ry, rz)
    px = h * SC * 1.1
    # 厚度：沿法线往后叠若干层，越往后越暗，层与层之间留出细亮线（参考视频里的"金属侧边"）
    layer_rgb = np.zeros((VH, VW, 3), np.float32); layer_a = np.zeros((VH, VW, 1), np.float32)
    depth = h * .07; N = 12
    mask = mips['mask'].get(px)
    for k in range(N, 0, -1):
        z = depth * k / N
        shade = .45 + .45 * (1 - k / N) + (.12 if k % 3 == 0 else 0)
        col = np.array([.10, .55, .95], np.float32) * shade + (.15 if k % 3 == 0 else 0)
        warp_into(layer_rgb, layer_a, mask, project(cx, cy, h, R, z), mult=np.clip(col, 0, 1))
    front = project(cx, cy, h, R, 0)
    warp_into(layer_rgb, layer_a, mips['sharp'].get(px), front)
    if g > 0.01:
        warp_into(layer_rgb, layer_a, mips['glow'].get(px), front, opacity=g)
    canvas[:] = canvas * (1 - layer_a) + layer_rgb                # layer_rgb 已按透明度预乘

def sprite(r):
    n = int(r * 8) | 1; c = n // 2
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((x - c) ** 2 + (y - c) ** 2)
    core = np.clip(1 - d / r, 0, 1); halo = np.exp(-(d / (r * 2.2)) ** 2) * .55
    a = np.clip(core + halo, 0, 1)
    return a

def render(end_png, out_mp4):
    bg = cv2.resize(rd(os.path.join(A, 'emb_bg.jpg'), cv2.IMREAD_COLOR), (VW, VH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    rays = rd(os.path.join(A, 'rays.png')).astype(np.float32) / 255
    end = cv2.resize(rd(end_png, cv2.IMREAD_COLOR), (VW, VH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    em = rd(os.path.join(A, 'emblem.png')); gl = rd(os.path.join(A, 'emblem_glow.png'))
    gl = cv2.resize(gl, (em.shape[1], em.shape[0]), interpolation=cv2.INTER_CUBIC)
    mk = em.copy(); mk[..., :3] = 255
    mk[..., 3] = cv2.dilate(mk[..., 3], np.ones((5, 5), np.uint8))
    mips = {'sharp': Mip(em), 'glow': Mip(gl), 'mask': Mip(mk)}
    rnd = np.random.default_rng(3)
    parts = [(rnd.uniform(0, VW), rnd.uniform(0, VH), rnd.uniform(-40, 40), rnd.uniform(-60, -10),
              rnd.uniform(3, 7), rnd.uniform(.35, .9)) for _ in range(22)]
    sprites = {}
    ff = shutil.which('ffmpeg')
    proc = subprocess.Popen([ff, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{VW}x{VH}', '-r', str(FPS),
                             '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', '-level', '4.2', '-g', '60', '-pix_fmt', 'yuv420p',
                             '-movflags', '+faststart', out_mp4], stdin=subprocess.PIPE)
    total = int((T_END + T_HOLD) * FPS) + 1
    SUB = 2                                                       # 运动模糊子帧
    for fi in range(total):
        t0 = fi / FPS
        acc = np.zeros((VH, VW, 3), np.float32)
        for si in range(SUB):
            t = min(t0 + si / (SUB * FPS) * .6, T_END)
            fr = bg.copy()
            rs = np.interp(t, [r[0] for r in RAYS], [r[1] for r in RAYS]) * SC
            ang = 12 * (1 - t / T_END)
            M = cv2.getRotationMatrix2D((rays.shape[1] / 2, rays.shape[0] / 2), ang, rs / rays.shape[1])
            M[0, 2] += 800 * SC - rays.shape[1] / 2; M[1, 2] += 330 * SC - rays.shape[0] / 2
            rw = cv2.warpAffine(rays, M, (VW, VH))
            fr = fr * (1 - rw[..., 3:4]) + rw[..., :3] * rw[..., 3:4]
            pa = np.clip(1 - (t - 2.4) / .8, 0, 1)                 # 光点最后淡出（下一页会重新出现）
            for (x, y, vx, vy, r, a) in parts:
                xx, yy = int(x + vx * t), int(y + vy * t)
                key = round(r)
                if key not in sprites: sprites[key] = sprite(key)
                sp = sprites[key]; n = sp.shape[0]; c = n // 2
                x0, y0 = xx - c, yy - c
                if x0 < 0 or y0 < 0 or x0 + n > VW or y0 + n > VH: continue
                al = (sp * a * pa)[..., None]
                fr[y0:y0 + n, x0:x0 + n] = fr[y0:y0 + n, x0:x0 + n] * (1 - al) + np.array([.55, .86, 1.0]) * al
            draw_emblem(fr, state(t), mips)
            acc += fr
        frame = acc / SUB
        k = np.clip((t0 - (T_END - T_FADE)) / T_FADE, 0, 1)        # 结尾淡入到 PPT 落定画面
        k = k * k * (3 - 2 * k)
        frame = frame * (1 - k) + end * k
        proc.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()
    return (T_END + T_HOLD)

if __name__ == '__main__':
    import sys
    render(sys.argv[1], sys.argv[2])
