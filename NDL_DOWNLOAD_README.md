# 日本国立国会图书馆自动下载器 使用说明

## 版本信息: v3.0 (2026-03-16)

## 🌟 核心功能

- ✅ **EXE 开箱即用**：提供打包好的 `NdlDownloaderPro.exe`，无需安装 Python 环境。
- ✅ **智能合并修复**：优化了文件合并逻辑，彻底解决了"Permission denied"权限报错问题。
- ✅ **自动分段下载**：突破 100 页限制，自动分段下载全书。
- ✅ **批量下载**：支持导入 `urls.txt` 或直接拖拽文本文件进行批量任务。
- ✅ **断点续传**：下载中断后再次运行，自动跳过已完成的部分，只下载剩余章节。
- ✅ **进度保存**：自动记录下载历史，避免重复下载。

---

## 📥 使用方法 (推荐：EXE版本)

### 1. 准备 Chrome 浏览器

本程序需要控制本地开启了调试模式的 Chrome。

**第一步：启动 Chrome**
请使用以下命令启动 Chrome（或者在快捷方式属性的目标后添加参数）：

**Windows PowerShell:**
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222"
```

**Windows CMD:**
```batch
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**第二步：登录 NDL**
在打开的浏览器中访问 [https://dl.ndl.go.jp/ja/](https://dl.ndl.go.jp/ja/) 并登录账号。
*注意：必须登录才能下载受限书籍。*

### 2. 运行下载器

进入 `dist` 文件夹，双击运行 `NDLDownloader.exe`。

**三种交互模式：**
1.  **单本模式**：看到提示后，直接粘贴书籍 URL 回车。
2.  **文件模式**：将包含链接的 `.txt` 文件直接拖入命令行窗口。
3.  **默认列表**：如果在 EXE 同级目录下有 `urls.txt`（每行一个链接），程序启动时会自动识别并询问是否加载。

---

## 🐍 使用方法 (源码运行)

如果您需要修改代码或在非 Windows 环境运行：

### 1. 安装依赖

推荐使用 conda 环境：
```bash
conda create -n ndl python=3.9
conda activate ndl
pip install -r requirements.txt
```
*特别注意：PDF合并功能依赖 `pycryptodome`。请勿安装旧版的 `crypto` 或 `pycrypto`，它们会导致冲突。*

### 2. 运行脚本

```bash
python ndl_auto_downloader.py
```

## 📂 文件结构说明

- `NDLDownloader.exe`: 主程序（在 dist 目录下）
- `download_history.json`: 进度记录文件（**重要**：如果下载中断，请保留此文件以支持断点续传）
- `urls.txt`: 批量下载列表模板
- `downloads/`: 下载目录
  - `书名.pdf`: 最终下载合并好的文件
  - `书名/`: 临时文件夹（下载过程中存放分段PDF，合并成功后会自动删除）

## ❓ 常见问题

**Q: 合并时报错 "Permission denied"？**
A: v3.0 版本已修复此问题。现在临时文件存放在文件夹中，合并完成后生成 PDF 文件并删除文件夹，不会产生命名冲突。

**Q: 只有分段文件，没有合并？**
A: 请检查是否安装了 `pycryptodome`。如果缺少解密库，程序会保留分段文件以防数据丢失。修复依赖后重新运行即可触发合并。
