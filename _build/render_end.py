# -*- coding: utf-8 -*-
"""结尾页动态背景（无缝循环视频）：光芒缓慢旋转、金色纹饰轮反向旋转、祥云轻摆、
金色光点上升闪烁、团徽呼吸光晕与流光、整屏柔光扫过。文字仍是 PPT 里可编辑的对象，叠在视频上面。
各运动的周期都整除循环时长，首尾帧完全一致，循环播放时看不出接缝。"""
import os, math, shutil, subprocess
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, '_build', 'assets')
VW, VH, FPS, LOOP = 1920, 1080, 60, 20.0
SC = VW / 1600

def rd(p): return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)

def rgba(name, w, h=None):
    im = rd(os.path.join(A, name)); h = h or w
    im = cv2.resize(im, (int(round(w)), int(round(h))), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    if im.shape[2] == 3: im = np.dstack([im, np.ones(im.shape[:2], np.float32)])
    return im

def over(dst, src, x, y, opacity=1.0):
    """src(RGBA) 左上角放在 (x, y)，支持亚像素位置（缓慢移动时不会一格一格地跳），自动裁剪到画面内。"""
    ix, iy = math.floor(x), math.floor(y); fx, fy = x - ix, y - iy
    if fx > 1e-3 or fy > 1e-3:
        M = np.float32([[1, 0, fx], [0, 1, fy]])
        src = cv2.warpAffine(src, M, (src.shape[1] + 1, src.shape[0] + 1), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    h, w = src.shape[:2]; x, y = ix, iy
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, VW), min(y + h, VH)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; a = s[..., 3:4] * opacity
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a

def rotated(src, ang, cx, cy):
    """把方形 RGBA 图绕自身中心旋转后，中心对准画面 (cx, cy)。"""
    n = src.shape[0]
    M = cv2.getRotationMatrix2D((n / 2, n / 2), ang, 1.0)
    M[0, 2] += cx - n / 2; M[1, 2] += cy - n / 2
    return cv2.warpAffine(src, M, (VW, VH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

def render(out_mp4):
    bg = cv2.resize(rd(os.path.join(A, 'cover_bg.jpg')), (VW, VH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    rays = rgba('rays.png', 1600 * SC); deco = rgba('deco.png', 760 * SC)
    city = rgba('cover_city.png', VW, VH)
    cloud = rgba('cloud.png', 440 * SC, 264 * SC); cloud_f = cloud[:, ::-1].copy()
    emb = rgba('emblem.png', 250 * SC)
    a = emb[..., 3]
    halo = cv2.GaussianBlur(a, (0, 0), 18 * SC)
    halo_rgba = np.dstack([np.full(a.shape + (3,), [.35, .8, 1.0], np.float32), np.clip(halo * 1.6, 0, 1)])
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    ey, ex = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
    rnd = np.random.default_rng(12)
    parts = [dict(x=rnd.uniform(60, VW - 60), y=rnd.uniform(0, VH), k=int(rnd.integers(1, 3)), r=rnd.uniform(2.5, 6.5),
                  ph=rnd.uniform(0, 1), tw=int(rnd.integers(2, 5)), sway=rnd.uniform(8, 24)) for _ in range(46)]
    def spr(r):
        n = int(r * 9) | 1; c = n // 2
        y, x = np.mgrid[0:n, 0:n].astype(np.float32); d = np.sqrt((x - c) ** 2 + (y - c) ** 2)
        al = np.clip(np.clip(1 - d / r, 0, 1) + np.exp(-(d / (r * 2.4)) ** 2) * .5, 0, 1)
        return np.dstack([np.full((n, n, 3), [.62, .88, 1.0], np.float32), al])
    sprites = {}
    ff = shutil.which('ffmpeg')
    proc = subprocess.Popen([ff, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{VW}x{VH}', '-r', str(FPS),
                             '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-profile:v', 'high', '-level', '4.2',
                             '-g', str(FPS * 2), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_mp4], stdin=subprocess.PIPE)
    N = int(LOOP * FPS)
    for fi in range(N):
        t = fi / FPS; u = t / LOOP; w = 2 * math.pi * u
        fr = bg.copy()
        # 整屏柔光：一道暖光从左向右缓缓扫过
        sx = (u * 1.6 - .3) * VW
        band = np.exp(-(((xx - sx) * .85 + (yy - VH / 2) * .5) / (VW * .16)) ** 2)[..., None] * .16
        fr = fr * (1 - band) + np.array([.62, .86, 1.0]) * band
        # 光芒：36 等分，每圈转 10° 正好无缝；亮度随呼吸起伏
        rw = rotated(rays, 10 * u, 800 * SC, 250 * SC)
        br = .85 + .15 * math.sin(w * 2)
        fr = fr * (1 - rw[..., 3:4] * br) + rw[..., :3] * rw[..., 3:4] * br
        dw = rotated(deco, -30 * u, 800 * SC, 250 * SC)          # 纹饰 30° 周期，反向慢转
        fr = fr * (1 - dw[..., 3:4]) + dw[..., :3] * dw[..., 3:4]
        over(fr, city, 0, 300 * SC)
        # 祥云：左右轻摆、上下浮动
        for (cx, cy, im, ph) in ((200, 700, cloud, 0), (1400, 700, cloud_f, .5)):
            dx = 14 * SC * math.sin(w + ph * 2 * math.pi); dy = 6 * SC * math.sin(2 * w + ph * 2 * math.pi)
            over(fr, im, cx * SC - im.shape[1] / 2 + dx, cy * SC - im.shape[0] / 2 + dy)
        # 金色光点：匀速上升（每圈升高整数倍画面高度）、左右摆动、闪烁
        for p in parts:
            y = (p['y'] - p['k'] * (VH + 80) * u) % (VH + 80) - 40
            x = p['x'] + p['sway'] * math.sin(w * 2 + p['ph'] * 6.283)
            op = .35 + .65 * (.5 + .5 * math.sin(w * p['tw'] + p['ph'] * 6.283))
            key = round(p['r'] * 2) / 2
            if key not in sprites: sprites[key] = spr(key)
            sp = sprites[key]; over(fr, sp, x - sp.shape[1] / 2, y - sp.shape[0] / 2, op)
        # 团徽：轻浮 + 呼吸光晕 + 流光（每圈两次）
        fy = 5 * SC * math.sin(w * 2)
        ex0 = 800 * SC - emb.shape[1] / 2; ey0 = 245 * SC - emb.shape[0] / 2 + fy
        over(fr, halo_rgba, ex0, ey0, .55 + .3 * math.sin(w * 2))
        e = emb.copy()
        for c0 in (.10, .60):
            g = (u - c0) / .07
            if -1.5 < g < 1.5:
                pos = (g + 1.5) / 3 * (a.shape[1] * 1.6) - a.shape[1] * .3
                gl = np.exp(-(((ex + ey * .5) - pos) / (a.shape[1] * .06)) ** 2)[..., None] * .75
                e[..., :3] = e[..., :3] * (1 - gl) + gl
        over(fr, e, ex0, ey0)
        proc.stdin.write((np.clip(fr, 0, 1) * 255).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()

if __name__ == '__main__':
    import sys
    render(sys.argv[1])
