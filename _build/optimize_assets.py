# -*- coding: utf-8 -*-
"""放映流畅度优化：把素材缩到"够 1080p/2K 投影用"的尺寸，并把 PPT 的实时发光效果预先烘焙成图片。
PowerPoint 做平滑切换(Morph)时每一帧都要重新缩放/旋转所有图片、实时计算发光，图片越大、发光越多越卡。"""
import os
import numpy as np, cv2

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

def rd(n): return cv2.imdecode(np.fromfile(os.path.join(A, n), np.uint8), cv2.IMREAD_UNCHANGED)
def wr(n, im, q=90):
    ext = os.path.splitext(n)[1]
    ok, b = cv2.imencode(ext, im, [cv2.IMWRITE_JPEG_QUALITY, q] if ext == '.jpg' else [cv2.IMWRITE_PNG_COMPRESSION, 7])
    b.tofile(os.path.join(A, n))

def shrink(n, maxdim, q=90):
    im = rd(n); h, w = im.shape[:2]; s = maxdim / max(h, w)
    if s < 1:
        im = cv2.resize(im, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
        wr(n, im, q)

def dot(alpha):
    """柔和发光金点（取代每个光点上的 PPT 实时发光效果）。"""
    n = 96; c = (n - 1) / 2
    y, x = np.mgrid[0:n, 0:n].astype(np.float32); d = np.sqrt((x - c) ** 2 + (y - c) ** 2) / (n / 2)
    core = np.clip((.30 - d) / .06, 0, 1)
    halo = np.exp(-(d / .42) ** 2) * .55
    a = np.clip(core + halo * (1 - core), 0, 1) * alpha
    col = np.zeros((n, n, 3), np.float32)
    col[:] = (60 / 255, 186 / 255, 1.0)                           # 外圈暖金
    col = col * (1 - core[..., None]) + np.array([130, 220, 255]) / 255 * core[..., None]
    return (np.dstack([col, a]) * 255).astype(np.uint8)

def emblem_halo():
    """团徽 + 烘焙的金色外发光，画布四周各留 12.5% 边距。"""
    em = cv2.resize(rd('emblem.png'), (960, 960), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    n = 1200; p = 120
    can = np.zeros((n, n, 4), np.float32); can[p:p + 960, p:p + 960] = em
    a = can[..., 3]
    g = cv2.GaussianBlur(a, (0, 0), 22) * .75
    out_a = a + g * (1 - a)
    gold = np.array([70 / 255, 200 / 255, 1.0], np.float32)
    rgb = (can[..., :3] * a[..., None] + gold * (g * (1 - a))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return (np.dstack([np.clip(rgb, 0, 1), out_a]) * 255).astype(np.uint8)

def run():
    for n in os.listdir(A):
        if n.startswith(('photo_', 'cover_bg', 'emb_bg')) and n.endswith('.jpg'): shrink(n, 2560, 90)
        elif n.startswith('ring_') and n.endswith('.jpg'): shrink(n, 2048, 88)
    for n, m in (('wheel.png', 2048), ('rays.png', 1800), ('cover_city.png', 2560), ('frame.png', 2560),
                 ('deco.png', 1400), ('emblem.png', 1200)):
        shrink(n, m)
    for k, al in enumerate((1.0, .75, .5)):
        wr(f'dot{k}.png', dot(al))
    wr('emblem_halo.png', emblem_halo())
    print('optimized')

if __name__ == '__main__':
    run()
