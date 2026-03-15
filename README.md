# NDL Downloader v2.0 (高级版-挂机王)

基于 DrissionPage 的日本国立国会图书馆（NDL）自动下载器。
解决国立国会图书馆登陆后下载文献每次最多100页、须手动输入下载页码并合并PDF文献的问题。一次导入，挂机下载，解放双手。
支持自动分段、批量任务、断点续传。

## ✨ 核心功能

- **🚀 自动分段下载**：自动处理 NDL 的 100 页下载限制，全自动分段下载。
- **📦 智能合并**：下载完成后自动将分段 PDF 合并为单一大文件（自动处理加密解密）。
- **🔄 断点续传**：意外中断没关系，再次运行会自动跳过已下载的章节，继续未完成的任务。
- **📑 批量下载**：支持导入 `urls.txt` 或直接拖拽文本文件，一次挂机下载多本书。
- **💾 进度保存**：自动记录所有下载历史和进度到 `download_history.json`。
- **⚡️ 无需配置**：已提供打包好的 EXE 版本，开箱即用。MaccOS 用户请自行编译。

## 📂 文件说明

- **NDLDownloader.exe** - 打包好的可执行程序（在 `dist` 目录下,`NdlDownloaderPro.exe`）。
- **ndl_auto_downloader.py** - 源代码脚本。
- **urls.txt** - 批量下载列表模板文件。
- **download_history.json** - 自动生成的进度记录（主要不要删除，用于断点续传）。
- **downloads/** - 下载文件的保存目录。

---

## 🚀 快速开始 (EXE版本)

### 1. 准备 Chrome 浏览器 

本程序通过控制本地 Chrome 浏览器运行，请先启动 Chrome 并开启调试端口 (9222)。

Tips：最好不要将浏览器最小化，可能导致谷歌浏览器进入节省内存的模式，导致任务超时。

**方式 A (PowerShell):**
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222"
```
*(请根据实际安装路径调整)*

**方式 B (快捷方式):**
右键 Chrome 快捷方式 -> 属性 -> 目标，在末尾添加空格和 `--remote-debugging-port=9222`，然后用此快捷方式启动。

### 2. 登录 NDL

启动带有调试端口的 Chrome 后，打开 [NDL Digital Collections](https://dl.ndl.go.jp/ja/) 并登录你的账号。

### 3. 运行下载器

双击运行 `dist/NDLDownloader.exe`。

**三种使用模式：**
1.  **单本下载**：直接粘贴书籍 URL 回车。
2.  **批量下载**：将包含 URLs 的 txt 文件拖入窗口。
3.  **默认列表**：如果在同目录下放了 `urls.txt`，程序会自动询问是否加载。

---

## 源码运行 (Python环境)

如果你想通过源码运行或修改：

### 1. 安装依赖

```bash
pip install -r requirements.txt
```
*注意：合并功能依赖 `PyPDF2` 和 `pycryptodome`，请确保正确安装。*

### 2. 运行

```bash
python ndl_auto_downloader.py
```

## ⚠️ 常见问题

- **合并失败 Permission denied？**
  - v3.0 已修复此问题。下载时会先保存在文件夹中，合并成功后生成 PDF 并删除文件夹。
- **如何开始批量下载？**
  - 编辑 `urls.txt`，每行放一个链接，然后运行程序。

更多详细说明请查看 `NDL_DOWNLOAD_README.md`

## 后续优化
1. Edge 浏览器支持
2. MacOS 兼容
3. GUI

## 说明
- 本项目基于 [DrissionPage](https://github.com/DrissionPage/NDL_Downloader) 创建，部分功能为AI生成。
- 本项目仅用于学习，请勿用于非法用途。