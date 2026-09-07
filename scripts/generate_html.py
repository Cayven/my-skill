#!/usr/bin/env python3
"""从 keyword-copy-template.html 生成自包含 HTML。

图片会以内嵌 base64 data URI 写入 HTML；关键词通过 JSON 序列化，避免引号/特殊字符破坏 JS。
"""
import argparse
import base64
import html
import json
import mimetypes
import re
from pathlib import Path


def safe_filename(text):
    text = re.sub(r'[\\/:*?"<>|\s]+', "_", text.strip())
    text = re.sub(r"_+", "_", text).strip("._")
    return text or "未命名单品"


def esc(text):
    return html.escape(str(text or ""), quote=True)


def image_data_uri(path):
    p = Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def kw_json(items):
    return json.dumps([str(x) for x in (items or [])], ensure_ascii=False, separators=(",", ":"))


def render(args):
    template = Path(args.template).read_text(encoding="utf-8")
    product = args.product.strip()
    brand = args.brand.strip() or "未识别"
    name = args.name.strip() or product[:12] or "未命名单品"
    care = args.care.strip()

    replacements = {
        "{{品牌}}": esc(brand),
        "{{品名}}": esc(name),
        "{{产品}}": esc(product),
        "{{单品名称}}": esc((brand + " " + product).strip()),
        "{{洗护建议}}": esc(care),
        "{{图片路径}}": image_data_uri(args.image),
        "{{风格定调关键词}}": kw_json(args.style),
        "{{色彩构析关键词}}": kw_json(args.color),
        "{{形制匠艺关键词}}": kw_json(args.craft),
        "{{本源溯往关键词}}": kw_json(args.origin),
        "{{衣脉沿革关键词}}": kw_json(args.evolution),
        "{{风尚流变关键词}}": kw_json(args.fashion),
        "{{地域文脉关键词}}": kw_json(args.region),
    }
    for k, v in replacements.items():
        template = template.replace(k, v)

    out = Path(args.output)
    if out.is_dir() or str(args.output).endswith("/"):
        out = out / f"{safe_filename(brand)}_{safe_filename(name)}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(template, encoding="utf-8")
    print(out)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--template", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--brand", default="")
    p.add_argument("--name", default="")
    p.add_argument("--product", default="")
    p.add_argument("--care", default="")
    for dim in ["style", "color", "craft", "origin", "evolution", "fashion", "region"]:
        p.add_argument(f"--{dim}", nargs="*", default=[])
    p.add_argument("--output", required=True)
    args = p.parse_args()
    render(args)


if __name__ == "__main__":
    main()
