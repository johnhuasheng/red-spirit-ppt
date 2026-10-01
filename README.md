# 团日活动 · 红色精神旋转 PPT

一份可直接放映的红色主题团日活动 PowerPoint：开场金光组装封面、团徽 3D 飞入、旋转扇面平滑切换、金色浮雕标题、动态循环结尾。

**在线观看：https://johnhuasheng.github.io/red-spirit-ppt/**（放映录像 + 逐页浏览 + 下载）

![封面](site/slides/01.jpg)

## 文件

| 路径 | 说明 |
|---|---|
| `团日活动_红色精神.pptx` | 成品 PPT（15 页，内嵌 3 段视频，约 43MB） |
| `index.html` + `site/` | 在线展示页：放映录像、逐页图片 |
| `_build/` | 生成 PPT 的脚本（Python + PowerPoint COM） |
| `images/hd/` | 高清原图与署名信息 `credits.txt` |
| `web-v1.html` | 最早的网页版复刻 |

## 放映

用 PowerPoint 2019 / Microsoft 365 打开（需支持“平滑”切换），按 F5。每单击一次进入下一页，页面内容随切换自动呈现；封面开场、团徽飞入、穿越团徽等过场自动播放。

## 重新生成

需要 Windows + PowerPoint、Python 3（`numpy`、`opencv-python`、`pywin32`）、Chrome、ffmpeg。

```bash
cd _build
python make_assets.py          # 生成背景、装饰、扇面贴图并压缩
python build_ppt.py --rerender # 渲染开场 / 飞入 / 结尾视频并生成 PPT
```

修改封面文字后需加 `--intro` 重新渲染开场动画，使其结尾与封面一致。

## 图片署名

照片来自 Wikimedia Commons，均为 CC BY-SA 4.0，经裁剪与调色：Morio（天安门夜景两张）、EditQ（华表、人民英雄纪念碑）、維基小霸王（人民大会堂、天安门城楼两张）。完整链接见 [`images/hd/credits.txt`](images/hd/credits.txt)。团徽、扇面、祥云等图形为程序绘制。
