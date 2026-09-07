# Outfit Point Line Network

中文穿搭单品深度解析 Skill。

它以“点线网”为底层思考框架，对服饰单品进行历史、时尚史、色彩、面料工艺、地域文化等维度的分析，并生成七维关键词与可离线打开的 HTML 关键词复制页。

## 适用场景

- 上传服装、鞋、帽、配饰等单品图片
- 分析单品的历史与文化脉络
- 提取穿搭关键词
- 建立个人穿搭知识库
- 生成可保存、可离线打开的关键词 HTML 页面

## 给 AI / Agent 的安装方式

将本仓库作为一个完整 Skill 获取，不要只读取 README：

Repository:
https://github.com/Cayven/my-skill

核心文件：
- `SKILL.md`：Skill 定义与执行规则
- `scripts/`：图片预处理与 HTML 生成脚本
- `references/`：方法论参考资料
- `assets/`：HTML 模板

安装时请保持以上目录结构，并优先读取 `SKILL.md`。

## 手动下载

GitHub 页面选择：

**Code → Download ZIP**

然后解压并保留完整目录结构。

## 本地脚本依赖

主要脚本使用 Python 3 与 Pillow；部分图片抠图功能可使用 `rembg`。

示例：

```bash
python3 scripts/preprocess_image.py input.jpg output.jpg whitebg 1024
python3 scripts/preprocess_image.py input.jpg output.jpg square 1024
```

生成 HTML：

```bash
python3 scripts/generate_html.py --help
```

## 设计原则

- 不把视觉推断冒充为历史事实
- 不确定的品牌、面料、产地等信息不杜撰
- HTML 图片使用 Base64 内嵌，支持离线打开
- 不依赖外部 CDN、字体或网络接口
