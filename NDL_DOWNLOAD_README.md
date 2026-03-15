# 日本国立国会图书馆自动下载器 使用说明

## 功能特点

- ✅ 自动分段下载书籍PDF（每次最多100页）
- ✅ 自动识别书籍页数和信息
- ✅ 支持断点续传（未测试）
- ✅ 下载进度保存（未测试）

## 使用前准备

### 1. 安装依赖(建议还是conda一个新环境)

```bash
pip install -r requirements.txt
```

如果之前只安装过 `DrissionPage`，请补装：

```bash
pip install pycryptodome
```

### 2. 启动Chrome浏览器

在使用脚本前，需要先启动Chrome浏览器并开启调试模式：

**Windows CMD:**
```batch
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Windows PowerShell:**
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222"
```

### 3. 登录网站

1. 打开Chrome后，访问：https://dl.ndl.go.jp/ja/
2. 使用您的账号登录（账号：E13817563）
3. 确保登录状态保持（自己登录也是可以的）

## 使用方法


适合单本书籍下载：

```bash
python ndl_auto_downloader.py
```

**使用流程：**
1. 运行脚本
2. 输入书籍URL（例如：https://dl.ndl.go.jp/ja/pid/1666316）
3. 脚本自动下载整本书
4. 可继续下载其他书籍或退出


## 注意事项

1. **浏览器状态**：确保Chrome浏览器已启动并保持登录状态
2. **下载位置**：文件会下载到脚本所在目录下的 `downloads/` 文件夹中
3. **网络稳定**：下载过程中保持网络连接稳定
4. **下载速度**：根据网络和文件大小，每个部分可能需要几秒到几分钟
5. **分批下载**：每本书最多100页为一个部分，大本书会分成多个PDF文件

## 常见问题

### Q1: 提示"连接浏览器失败"
**A:** 确保Chrome已使用`--remote-debugging-port=9222`参数启动

### Q2: 无法找到书籍页数
**A:** 可能是页面加载未完成，脚本会自动重试，或检查URL是否正确


### Q3: 如何合并分割的PDF文件
**A:** 可以使用PDF合并工具如：
- Python: `PyPDF2`库
- 在线工具: Smallpdf, ILovePDF等
- 本地软件: Adobe Acrobat, PDFtk等

### Q5: 提示"PyCryptodome is required for AES algorithm"
**A:** 当前Python环境缺少AES解密依赖，请执行：

```bash
pip install pycryptodome
```

或重新安装完整依赖：

```bash
pip install -r requirements.txt
```

## 技术参数

- 默认调试端口: 9222
- 每部分最大页数: 100
- 部分间等待时间: 5秒
- 下载超时时间: 10秒
- 书籍间等待时间: 10秒（批量模式）

## 脚本特性

### 基础版特性
- ✅ 自动连接浏览器
- ✅ 自动识别书籍信息
- ✅ 自动分段下载
- ✅ 简单易用的交互界面

### 高级版特性
- ✅ 基础版所有功能
- ✅ 批量下载支持
- ✅ 断点续传功能
- ✅ 进度保存和恢复
- ✅ 详细的下载日志
- ✅ 下载历史记录
- ✅ 更好的错误处理

## 更新日志

### v1.0.0 (2026-03-15)
- 初始版本发布
- 支持基础下载功能
- 支持批量下载和断点续传

## 许可证

本脚本仅供学习和研究使用，请遵守日本国立国会图书馆的使用条款。

## 联系方式

如有问题或建议，请联系开发者。