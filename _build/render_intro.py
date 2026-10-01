# -*- coding: utf-8 -*-
"""封面开场动画（预渲染 60fps）。素材是 PowerPoint 导出的封面"分阶段"画面，保证结尾与正式封面像素级一致：
  S0 背景  S1 +光芒/纹饰轮  S2 +天安门/祥云/金框/光点  S3 +团徽  S4 +标题  S5 完整封面
动画：暗场中一点金光亮起 → 光芒旋转展开、纹饰轮转入 → 金色光点向中心汇聚 → 闪光中团徽浮现 →
天安门剪影与祥云自下而上显现、金框描出 → 标题"团日活动"金光扫过显字 → 匾额由中间向两侧展开 → 落定。"""
import os, math, shutil, subprocess
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, '_build', 'assets')
VW, VH, FPS, DUR = 1920, 1080, 60, 4.6
SC = VW / 1600

def rd(p, flag=cv2.IMREAD_UNCHANGED): return cv2.imdecode(np.fromfile(p, np.uint8), flag)
def ss(a, b, t): x = np.clip((t - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def ease_out(a, b, t): x = np.clip((t - a) / (b - a), 0, 1); return 1 - (1 - x) ** 3

yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)

def layer_mask(cur, prev, k=14.0):
    d = np.abs(cur - prev).max(-1, keepdims=True)
    return np.clip(d * k, 0, 1)

def rotated(src, ang, scale, cx, cy):
    n = src.shape[0]
    M = cv2.getRotationMatrix2D((n / 2, n / 2), ang, scale)
    M[0, 2] += cx - n / 2; M[1, 2] += cy - n / 2
    return cv2.warpAffine(src, M, (VW, VH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

def comp(dst, rgba, op=1.0):
    a = rgba[..., 3:4] * op
    return dst * (1 - a) + rgba[..., :3] * a

def render(stage_pngs, out_mp4):
    S = [cv2.resize(rd(p, cv2.IMREAD_COLOR), (VW, VH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 for p in stage_pngs]
    M2 = layer_mask(S[2], S[1]); M4 = layer_mask(S[4], S[3]); M5 = layer_mask(S[5], S[4])
    rays = rd(os.path.join(A, 'rays.png')).astype(np.float32) / 255
    deco = rd(os.path.join(A, 'deco.png')).astype(np.float32) / 255
    emb = rd(os.path.join(A, 'emblem.png')).astype(np.float32) / 255
    egl = cv2.resize(rd(os.path.join(A, 'emblem_glow.png')), (emb.shape[1], emb.shape[0])).astype(np.float32) / 255
    rnd = np.random.default_rng(8)
    ecx, ecy = 800 * SC, 150 * SC
    parts = []
    for _ in range(70):
        ang = rnd.uniform(0, 6.283); r0 = rnd.uniform(700, 1300) * SC
        parts.append((ecx + r0 * math.cos(ang), ecy + 120 * SC + r0 * math.sin(ang) * .6, rnd.uniform(2, 5.5), rnd.uniform(0, .35)))
    def spr(r):
        n = int(r * 9) | 1; c = n // 2
        y, x = np.mgrid[0:n, 0:n].astype(np.float32); d = np.sqrt((x - c) ** 2 + (y - c) ** 2)
        return np.clip(np.clip(1 - d / r, 0, 1) + np.exp(-(d / (r * 2.4)) ** 2) * .5, 0, 1)[..., None]
    sprites = {}
    ff = shutil.which('ffmpeg')
    proc = subprocess.Popen([ff, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{VW}x{VH}', '-r', str(FPS),
                             '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', '-level', '4.2',
                             '-g', '60', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_mp4], stdin=subprocess.PIPE)
    N = int(DUR * FPS) + 1
    for fi in range(N):
        t = fi / FPS
        # ---- 背景：暗场中由中心向外亮起
        lit = ss(0.0, 1.3, t)
        r = np.sqrt(((xx - ecx) / (VW * .9)) ** 2 + ((yy - ecy * 1.6) / (VH * .9)) ** 2)
        reveal = np.clip((lit * 1.6 - r) / .45, 0, 1)[..., None]
        fr = S[0] * (.18 + .82 * reveal)
        # ---- 光芒：从小旋转放大展开；纹饰轮反向转入
        k = ease_out(.15, 1.6, t)
        if k > 0:
            fr = comp(fr, rotated(rays, 70 * (1 - k), (1700 * SC / rays.shape[0]) * (.15 + .85 * k), ecx, 230 * SC), k)
        k2 = ease_out(.45, 1.8, t)
        if k2 > 0:
            fr = comp(fr, rotated(deco, -90 * (1 - k2), (1000 * SC / deco.shape[0]) * (.55 + .45 * k2), 800 * SC, 330 * SC), k2)
        # ---- 天安门、祥云、金框、光点：自下而上显现
        k3 = ss(1.5, 2.6, t)
        if k3 > 0:
            wipe = np.clip(((VH - yy) / VH - (1 - k3 * 1.25)) / .25 + 1, 0, 1)[..., None] if k3 < 1 else 1
            m = M2 * wipe * k3
            fr = fr * (1 - m) + S[2] * m
        # ---- 光点汇聚
        pk = ease_out(.3, 1.45, t)
        if t < 1.6:
            for (x0, y0, rr, dl) in parts:
                q = np.clip((pk - dl) / (1 - dl), 0, 1) if pk > dl else 0
                x = x0 + (ecx - x0) * q; y = y0 + (ecy - y0) * q
                op = min(1, t / .3) * (1 - ss(1.3, 1.55, t))
                key = round(rr * 2) / 2
                if key not in sprites: sprites[key] = spr(key)
                sp = sprites[key]; n = sp.shape[0]; xi, yi = int(x) - n // 2, int(y) - n // 2
                if 0 <= xi and 0 <= yi and xi + n <= VW and yi + n <= VH:
                    a = sp * op
                    fr[yi:yi + n, xi:xi + n] = fr[yi:yi + n, xi:xi + n] * (1 - a) + np.array([.6, .88, 1.0]) * a
        # ---- 闪光 + 团徽浮现（放大回弹，珠光褪去）
        fl = math.exp(-((t - 1.45) / .16) ** 2)
        if fl > .01:
            g = np.exp(-(((xx - ecx) / (330 * SC)) ** 2 + ((yy - ecy) / (300 * SC)) ** 2))[..., None] * fl
            fr = fr * (1 - g * .85) + np.array([.82, .96, 1.0]) * g * .85
        ke = ease_out(1.35, 2.1, t)
        if ke > 0:
            over = 1 + .25 * math.sin(math.pi * min(1, (t - 1.35) / .75)) * (1 - ke)
            sc_ = (200 * SC / emb.shape[0]) * (.35 + .65 * ke) * over
            fr = comp(fr, rotated(emb, 0, sc_, ecx, ecy), min(1, (t - 1.35) / .25))
            gk = 1 - ss(1.6, 2.3, t)
            if gk > 0: fr = comp(fr, rotated(egl, 0, sc_, ecx, ecy), gk)
        # ---- 标题：金光由左向右扫过显字
        k4 = ss(2.2, 3.2, t)
        if k4 > 0:
            edge = (250 + 1100 * k4 * 1.15) * SC
            wipe = np.clip((edge - xx) / (90 * SC), 0, 1)[..., None]
            m = M4 * wipe
            fr = fr * (1 - m) + S[4] * m
            if k4 < 1:
                band = np.exp(-((xx - edge + 40 * SC) / (55 * SC)) ** 2)[..., None] * M4 * 1.2
                fr = np.clip(fr + band * np.array([.55, .85, 1.0]), 0, 1)
        # ---- 匾额、分隔线、英文、落款：由中间向两侧展开
        k5 = ease_out(3.0, 3.9, t)
        if k5 > 0:
            half = 820 * SC * k5
            m = M5 * np.clip((half - np.abs(xx - 800 * SC)) / (60 * SC), 0, 1)[..., None]
            fr = fr * (1 - m) + S[5] * m
        # ---- 最后淡入到完整封面（与下一页完全一致）
        kf = ss(DUR - .5, DUR - .05, t)
        fr = fr * (1 - kf) + S[5] * kf
        proc.stdin.write((np.clip(fr, 0, 1) * 255).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()

if __name__ == '__main__':
    import sys
    render(sys.argv[1:7], sys.argv[7])
