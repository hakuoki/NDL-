# NDL Downloader

日本国立国会图书馆自动下载器

## 包含文件

- **ndl_auto_downloader.py** - 基础版下载器
- **ndl_advanced_downloader.py** - 高级版下载器（支持批量下载、断点续传）
- **NDL_DOWNLOAD_README.md** - 详细使用说明

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果你之前只安装过 `DrissionPage`，请补装：

```bash
pip install pycryptodome
```

### 2. 启动Chrome浏览器

**Windows CMD:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Windows PowerShell:**
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222"
```

### 3. 登录网站

访问 https://dl.ndl.go.jp/ja/ 并登录

### 4. 运行下载器

**基础版：**
```bash
python ndl_auto_downloader.py
```

**高级版：**
```bash
python ndl_advanced_downloader.py
```

## 功能特点

✅ 自动分段下载（每次最多100页）
✅ 自动识别书籍信息
✅ 支持单本/批量下载
✅ 断点续传（高级版）
✅ 进度保存（高级版）

详细说明请查看 `NDL_DOWNLOAD_README.md`
