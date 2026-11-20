# 《内存一致性与缓存一致性入门》第二版翻译项目

原书：*A Primer on Memory Consistency and Cache Coherence, Second Edition*，Vijay Nagarajan、Daniel J. Sorin、Mark D. Hill、David A. Wood，2020。

## 阅读入口

- 浏览器阅读：打开 `output/reader/index.html`。无需联网，可按章阅读，支持全文搜索、字号调整、四种中英文显示模式、夜间主题和续读。
- 电子书阅读器：导入 `output/内存一致性与缓存一致性入门_第二版_中英对照.epub`。采用 EPUB 3 流式排版，英文原文与中文译文上下对应。
- 复制到其他设备：解压 `output/中英对照_离线阅读版.zip` 的全部内容，再打开其中的 `reader/index.html`。需保留同目录下的 `assets` 文件夹。

手机上自动使用上下对照；宽屏默认左右对照。页面顶部的阅读模式按钮可循环切换左右对照、上下对照、仅中文和仅英文。每个原书页面后有完整原版面的查看入口。图表与公式均可放大。

## 内容与范围

覆盖卷首、版权页、丛书目录、摘要、原书目录、两版前言、全部 11 章及各章参考文献、作者简介。底本共 296 个 PDF 页面；正文原书页码 1–274 对应 PDF 第 23–296 页。空白页不生成翻译块。

翻译采用计算机体系结构领域常用的简体中文学术表述，区分“内存一致性”（memory consistency）与“缓存一致性”（cache coherence）。统一术语及使用原则保存在 `glossary.json`，阅读版也提供可阅读的术语表。

译文保留 2020 年第二版的技术结论、参考文献和时代背景。原文中的“目前”、未来展望和作者履历均按成书时的语境翻译。必要的纠错说明以“译注”标出。代码、消息名、变量、状态缩写和文献标识保留原文。

图表保留英文原貌，其文字在相应位置提供中文对照。协议表格的译文在需要时展开为逐状态、逐事件的说明，便于窄屏阅读。PDF 提取可能破坏公式符号、删除线、上下标或表格顺序，因此另附原版面作为核对依据。跨页原段落会按原页拆成相邻对照块。

## 项目结构

| 路径 | 用途 |
| --- | --- |
| `primer2020_2nd_edition.pdf` | 用户提供的原书，不修改 |
| `source/ch01.json` 至 `source/ch11.json` | 按章提取的英文文本、原页码、块编号及版面坐标 |
| `source/front.json`、`source/bio.json` | 卷首和作者简介的英文底稿 |
| `translations/ch01.json` 至 `translations/ch11.json` | 可独立修订的逐章中文译文 |
| `translations/front.json`、`translations/bio.json` | 卷首和作者简介译文 |
| `glossary.json` | 统一术语及翻译规范 |
| `scripts/` | 提取、原版面渲染、阅读版构建与校验工具 |
| `output/reader/` | 离线阅读版和图像资源 |
| `output/validation.json` | 最后一次构建的逐章覆盖检查 |
| `qa/` | 排版抽查图、浏览器功能检查及文字审查记录 |

## 修订与重建

译文文件采用 UTF-8 JSON，键是固定的原文块编号，例如 `p023b03`，值是对应中文。修订译文时保留键名。块编号中的页码为 PDF 页面序号，不是印刷页码。

项目已包含构建需要的图像。仅修改中文译文或术语表后，使用 Python 运行：

```powershell
python scripts/build_book.py
```

该命令同时更新浏览器阅读版、EPUB 和离线阅读压缩包。正式构建要求每个源块都存在非空译文；缺项时退出，不生成完整版本。`--preview` 仅供项目制作过程中的排版检查使用。

若要从原 PDF 重新生成英文底稿和图像，需要 `pdfplumber` 和 `Pillow`：

```powershell
python scripts/extract_book.py
python scripts/render_sources.py
python scripts/prepare_layout.py
python scripts/build_book.py
```

注意：重新提取可能改变文本分块。若改变提取逻辑，应先备份既有底稿和译文，并检查块编号与译文的对应关系。

检查命令：

```powershell
python scripts/audit_translation.py
python scripts/validate_outputs.py
```

桌面／手机布局与交互检查，以及封面生成，使用 Node.js、Playwright 和 Microsoft Edge。安装 Node.js 与 Microsoft Edge 后，在项目根目录安装依赖并运行：

```powershell
npm install
npm run qa:reader
npm run build:cover
```

`qa:reader` 检查现有阅读版，并将截图与检查结果写入 `qa/`；`build:cover` 更新 `output/reader/assets/cover.png`。封面更新后，运行 `python scripts/build_book.py`，将新封面打包到 EPUB 和离线阅读压缩包中。

原著版权 © 2020 Morgan & Claypool。完整出版信息和原版权声明保留在卷首中。
