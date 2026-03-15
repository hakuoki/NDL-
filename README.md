# NDL Downloader

基于DrissionPage库的日本国立国会图书馆文献（仅登录可用）自动下载器

## 包含文件

- **ndl_auto_downloader.py** - 输入URL自动下载需要登录才能下载的日文文献，每次下载最多100页，全部下载完毕后合并文件。
- **NDL_DOWNLOAD_README.md** - 详细使用说明

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果你之前只安装过 `DrissionPage`，请补装：（NDL的PDF经过加密，合并操作需要解密）

```bash
pip install pycryptodome
```

### 2. 启动Chrome浏览器（调试模式）

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

```bash
python ndl_auto_downloader.py
```


## 功能特点

✅ 自动分段下载（每次最多100页）
✅ 自动识别书籍信息（页数、书名）
✅ 支持单本/批量下载
✅ 断点续传（测试中）
✅ 进度保存（测试中）

详细说明请查看 `NDL_DOWNLOAD_README.md`
