#!/usr/bin/env python3
"""穿搭单品图片预处理。

用法:
  python preprocess_image.py INPUT OUTPUT [whitebg|square] [SIZE]

whitebg: 优先 rembg 抠图并换纯白底；没有 rembg 时使用稳健的白底/主体检测，绝不直接假装完成抠图。
square: 保留原图内容，按短边中心裁剪成正方形，不做主体检测，避免误裁真人/场景图。
"""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter


def load_rgb(path):
    return Image.open(path).convert("RGB")


def optional_rembg(path):
    try:
        from rembg import remove, new_session
        from io import BytesIO
        session = new_session("u2net")
        data = Path(path).read_bytes()
        out = remove(data, session=session)
        return Image.open(BytesIO(out)).convert("RGBA"), True
    except ImportError:
        return None, False
    except Exception as exc:
        print(f"[警告] rembg 执行失败，改用白底主体检测: {exc}")
        return None, False


def whitebg_fallback(img):
    """无 rembg 时：识别近白背景与主要非白区域，生成透明主体。
    这是保守降级：如果无法可靠识别，则保留原图并以白底输出，而不是伪造抠图成功。
    """
    import numpy as np
    arr = np.asarray(img).astype("int16")
    # 与纯白的最大通道差；同时避免把浅灰商品全部当背景。
    diff = 255 - arr.min(axis=2)
    mask = diff > 18
    # 去除非常小的噪点/文字碎片（不依赖 scipy）。
    m = Image.fromarray((mask * 255).astype("uint8"), "L")
    m = m.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(5))
    bbox = m.getbbox()
    if not bbox:
        return img.convert("RGBA"), False
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    area_ratio = (bw * bh) / (img.width * img.height)
    # 太小或几乎覆盖全图时，无法可靠判断主体。
    if area_ratio < 0.03 or area_ratio > 0.92:
        return img.convert("RGBA"), False
    rgba = img.convert("RGBA")
    rgba.putalpha(m)
    return rgba, True


def crop_square_fit(img, bbox, padding_ratio=0.15):
    """以 bbox 为主体做正方形 crop；越界时平移 crop，而不是缩小导致主体被裁切。"""
    x0, y0, x1, y1 = bbox
    subject_w = max(1, x1 - x0)
    subject_h = max(1, y1 - y0)
    side = int(round(max(subject_w, subject_h) * (1 + 2 * padding_ratio)))
    side = min(side, img.width, img.height)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    left = int(round(cx - side / 2))
    top = int(round(cy - side / 2))
    left = max(0, min(left, img.width - side))
    top = max(0, min(top, img.height - side))
    return img.crop((left, top, left + side, top + side))


def alpha_bbox(rgba):
    alpha = rgba.getchannel("A")
    # 轻微阈值，避免透明边缘/压缩噪点撑大 bbox
    alpha = alpha.point(lambda p: 255 if p > 12 else 0)
    return alpha.getbbox()


def process_whitebg(input_path, output_path, size):
    original = load_rgb(input_path)
    rgba, used_rembg = optional_rembg(input_path)
    if rgba is None:
        rgba, detected = whitebg_fallback(original)
        if detected:
            print("[whitebg] rembg 不可用，使用近白背景主体检测降级")
        else:
            print("[白底降级] 无法可靠识别主体，保留原图内容并居中裁剪；请人工检查")
            rgba = original.convert("RGBA")

    bbox = alpha_bbox(rgba)
    if bbox:
        cropped = crop_square_fit(rgba, bbox, 0.15)
        bg = Image.new("RGB", cropped.size, (255, 255, 255))
        bg.paste(cropped, mask=cropped.getchannel("A"))
    else:
        side = min(original.width, original.height)
        left = (original.width - side) // 2
        top = (original.height - side) // 2
        bg = original.crop((left, top, left + side, top + side))

    final = bg.resize((size, size), Image.Resampling.LANCZOS)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, "JPEG", quality=95, optimize=True)
    print(f"[whitebg] 输出: {output_path} ({size}x{size}), rembg={'yes' if used_rembg else 'no'}")
    return output_path


def process_square(input_path, output_path, size):
    """严格保留原图信息：仅按短边中心裁成正方形，不猜主体。"""
    img = load_rgb(input_path)
    side = min(img.width, img.height)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    cropped = img.crop((left, top, left + side, top + side))
    final = cropped.resize((size, size), Image.Resampling.LANCZOS)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, "JPEG", quality=95, optimize=True)
    print(f"[square] 输出: {output_path} ({size}x{size})")
    return output_path


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    input_path, output_path = sys.argv[1:3]
    mode = sys.argv[3] if len(sys.argv) >= 4 else "whitebg"
    size = int(sys.argv[4]) if len(sys.argv) >= 5 else 1024
    if mode not in {"whitebg", "square"}:
        raise SystemExit("mode 必须是 whitebg 或 square")
    if size < 256 or size > 4096:
        raise SystemExit("size 应在 256-4096 之间")
    return process_whitebg(input_path, output_path, size) if mode == "whitebg" else process_square(input_path, output_path, size)


if __name__ == "__main__":
    raise SystemExit(main())
