#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本国立国会图书馆自动下载器
自动分段下载书籍PDF，每次最多100页
支持批量下载、断点续传、进度保存
"""

import sys
import io
import json
import os
import time
import shutil
import re
from datetime import datetime
from DrissionPage import ChromiumPage
from PyPDF2 import PdfWriter
from PyPDF2.errors import DependencyError

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_application_path():
    """获取程序运行目录（兼容打包后的exe）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class NDLAutoDownloader:
    def __init__(self, port=9222):
        """
        初始化下载器

        Args:
            port: Chrome调试端口，默认9222
        """
        self.port = port
        self.browser = None
        self.tab = None
        self.base_dir = get_application_path()
        self.download_dir = os.path.join(self.base_dir, 'downloads')
        self.history_file = os.path.join(self.base_dir, 'download_history.json')
        self.history = self.load_history()

        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)

    def load_history(self):
        """加载下载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ 加载历史记录失败: {e}")
                return {}
        return {}

    def save_history(self):
        """保存下载历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ 保存历史记录失败: {e}")

    def update_history(self, url, title=None, total_pages=None, part_num=None, completed=False):
        """更新单条历史记录"""
        if url not in self.history:
            self.history[url] = {
                'title': title,
                'total_pages': total_pages,
                'downloaded_parts': [],
                'completed': False,
                'last_updated': str(datetime.now())
            }
        
        record = self.history[url]
        record['last_updated'] = str(datetime.now())
        
        if title: record['title'] = title
        if total_pages: record['total_pages'] = total_pages
        if completed: record['completed'] = True
        
        if part_num is not None:
            if 'downloaded_parts' not in record:
                record['downloaded_parts'] = []
            if part_num not in record['downloaded_parts']:
                record['downloaded_parts'].append(part_num)
                record['downloaded_parts'].sort()
        
        self.save_history()

    def connect_browser(self):
        """连接到已打开的Chrome浏览器"""
        try:
            print(f"尝试连接到本地Chrome浏览器 (端口 {self.port})...")
            # 使用地址格式连接到已打开的Chrome
            self.browser = ChromiumPage(addr_or_opts=f'127.0.0.1:{self.port}')
            self.tab = self.browser
            print("✓ 成功连接到Chrome浏览器")
            print(f"  当前标签页URL: {self.tab.url}")
            print(f"  当前标签页标题: {self.tab.title}")
            return True
        except Exception as e:
            print(f"✗ 连接浏览器失败: {e}")
            print("\n请按以下步骤操作:")
            print("1. 关闭所有Chrome浏览器")
            print("2. 运行以下命令启动Chrome:")
            print(f"   Start-Process 'chrome.exe路径' -ArgumentList '--remote-debugging-port={self.port}'")
            print("3. 在Chrome中登录并访问要下载的页面")
            print("4. 再次运行此程序")
            return False

    def get_book_info(self, url):
        """
        获取书籍信息

        Args:
            url: 书籍页面URL

        Returns:
            dict: 包含标题、作者、总页数等信息的字典
        """
        print(f"正在访问: {url}")
        # 如果已经在该页面，就不重复跳转
        if url not in self.tab.url:
            self.tab.run_js(f"window.location.href = '{url}'")
            time.sleep(3)

        # 获取页面信息
        body_text = self.tab('t:body').text

        # 解析页数
        total_pages = 0
        if '/374' in body_text or '/374' in str(body_text):
            total_pages = 374
        elif '/226' in body_text or '/226' in str(body_text):
            total_pages = 226
        else:
            # 尝试从页面元素中提取页数
            try:
                page_info = self.tab.ele('xpath://input[@aria-label="コマ番号"]')
                if page_info:
                    max_attr = page_info.attr('max')
                    if max_attr:
                        total_pages = int(max_attr)
            except:
                pass

        # 提取标题 - 优先使用标签页标题
        title = "未知标题"
        try:
            # 优先使用标签页标题（最准确的书名），去掉后缀
            tab_title = self.tab.title
            if tab_title:
                # 去掉" - 国立国会図書館デジタルコレクション"后缀
                if ' - ' in tab_title:
                    title = tab_title.split(' - ')[0]
                elif '国立国会図書館' not in tab_title:
                    title = tab_title
                print(f"  使用标签页标题: {title}")

            # 如果标签页标题不合适，尝试从页面元素获取タイトル
            if title == "未知标题":
                # 查找 "タイトル" 后面的内容
                title_match = re.search(r'タイトル\s*([^\n\r]+)', body_text)
                if title_match:
                    title = title_match.group(1).strip()
                    print(f"  从タイトル字段提取: {title}")
        except Exception as e:
            print(f"  获取标题时出错: {e}")

        # 清理文件名中不合法的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '_')

        print(f"  书名: {title}")
        print(f"  总页数: {total_pages}")

        return {
            'title': title,
            'total_pages': total_pages,
            'url': url
        }

    def open_print_dialog(self):
        """打开印刷对话框"""
        try:
            # 尝试多种方式找到印刷按钮
            selectors = [
                'xpath://button[@id="open-printing-modal"]',
                'xpath://button[contains(text(), "印刷")]',
                'css:.information-header-nav-print-guide'
            ]

            for selector in selectors:
                try:
                    print_button = self.tab.ele(selector)
                    if print_button:
                        print_button.click()
                        # 等待对话框出现
                        time.sleep(3)
                        print("  ✓ 已打开印刷对话框")
                        return True
                except:
                    continue

            print("✗ 未找到印刷按钮")
            return False
        except Exception as e:
            print(f"✗ 打开印刷对话框失败: {e}")
            return False

    def set_page_range(self, start_page, end_page):
        """
        设置页码范围

        Args:
            start_page: 起始页码
            end_page: 结束页码
        """
        try:
            # 先尝试通过JavaScript选择"範囲を指定"选项
            js_code = f'''
            // 查找并点击"範囲を指定"选项
            const radio = document.querySelector('input[id="printing-modal-range-specific"]');
            if (radio) {{
                radio.click();
                return '成功选择范围指定选项';
            }}
            return '未找到范围指定选项';
            '''
            result = self.tab.run_js(js_code)
            # print(f"  JS执行结果: {result}")
            time.sleep(1)

            # 然后输入页码范围 - 尝试多种方式
            page_range_str = f"{start_page}-{end_page}"
            print(f"  准备输入页码范围: {page_range_str}")

            # 方式1: 通过id直接输入
            try:
                range_input = self.tab.ele('xpath://input[@id="range-specific-input"]')
                if range_input:
                    range_input.clear()
                    range_input.input(page_range_str)
                    time.sleep(0.5)
                    # print(f"  ✓ 方式1成功输入页码")
                    return True
            except:
                pass

            # 方式2: 通过JavaScript输入
            try:
                js_code2 = f'''
                const input = document.querySelector('input[id="range-specific-input"]');
                if (input) {{
                    input.value = "{page_range_str}";
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return 'JS输入成功';
                }}
                return '未找到输入框';
                '''
                result2 = self.tab.run_js(js_code2)
                # print(f"  JS输入结果: {result2}")
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"  JS输入失败: {e}")

            print(f"  设置页码范围: {start_page}-{end_page}")
            return True
        except Exception as e:
            print(f"✗ 设置页码范围失败: {e}")
            return False

    def start_print(self, part_num):
        """
        开始印刷/下载

        Args:
            part_num: 部分编号，用于文件命名
        """
        try:
            # 点击"印刷用ファイルを開く"按钮
            js_code = '''
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                const text = btn.textContent || '';
                if (text.includes('印刷用ファイルを開く') || text.includes('ファイルを開く')) {
                    btn.click();
                    return '已点击印刷用ファイルを開く';
                }
            }
            return '未找到印刷用ファイルを開く按钮';
            '''
            result = self.tab.run_js(js_code)
            # print(f"  JS执行结果: {result}")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"✗ 点击印刷按钮失败: {e}")
            return False

    def wait_pdf_generated(self, timeout=60):
        """
        等待PDF生成完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            str: PDF链接文本，失败返回None
        """
        print(f"  等待PDF生成完成（最多{timeout}秒）...", end='', flush=True)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 检查页面是否出现"PDFファイルを開く"链接
                body_text = self.tab('t:body').text

                if 'PDFファイルを開く' in body_text:
                    print(" ✓ PDF生成完成")
                    # 额外等待1秒确保链接完全加载
                    time.sleep(1)
                    return 'PDFファイルを開く'

                if '印刷用ファイルを作成しました' in body_text:
                    print('+', end='', flush=True)
            except Exception as e:
                pass

            time.sleep(2)
            print('.', end='', flush=True)

        print("\n  ✗ PDF生成超时")
        return None

    def open_pdf_page(self):
        """
        打开PDF页面

        Returns:
            str: PDF下载URL，失败返回None
        """
        try:
            print("  查找PDF下载链接...")

            # 不点击链接，直接获取PDF链接的href属性
            links = self.tab.eles('tag:a')
            pdf_url = None

            for link in links:
                link_text = link.text or ''
                if 'PDFファイルを開く' in link_text:
                    # 获取href属性
                    href = link.attr('href')
                    if href:
                        pdf_url = href
                        print(f"  ✓ 找到PDF链接")
                        # print(f"  PDF URL: {pdf_url}")
                        break

            if pdf_url:
                # 处理相对URL
                if not pdf_url.startswith('http'):
                    if pdf_url.startswith('/'):
                        base_url = 'https://dl.ndl.go.jp'
                        pdf_url = base_url + pdf_url
                    else:
                        # 如果是相对路径，从当前页面URL构建
                        current_url = self.tab.url
                        from urllib.parse import urljoin
                        pdf_url = urljoin(current_url, pdf_url)

                # print(f"  ✓ 完整PDF URL: {pdf_url}")
                return pdf_url
            else:
                print("  ✗ 未找到PDF链接")
                return None

        except Exception as e:
            print(f"  ✗ 获取PDF链接失败: {e}")
            return None

    def download_pdf_directly(self, pdf_url, part_num, title):
        """
        直接下载PDF文件

        Args:
            pdf_url: PDF下载URL
            part_num: 部分编号
            title: 书籍标题

        Returns:
            bool: 是否下载成功
        """
        try:
            import urllib.request
            import urllib.parse
            import ssl

            # 处理SSL证书问题
            ssl._create_default_https_context = ssl._create_unverified_context

            print(f"  开始下载PDF文件...")

            # 创建书籍专属目录
            # 修改为：downloads/{title}/ (不带.pdf后缀，避免与最终文件冲突)
            book_dir = os.path.join(self.download_dir, title)
            os.makedirs(book_dir, exist_ok=True)

            # 尝试提取书籍ID
            book_id = "unknown"
            match = re.search(r'/digidepo_(\d+)_', pdf_url)
            if match:
                book_id = match.group(1)

            # 生成文件名
            filename = f"{title}_{book_id}_{part_num:04d}.pdf"
            filepath = os.path.join(book_dir, filename)

            # 下载文件
            print(f"  下载到: {filepath}")
            
            # 使用简单的进度显示
            def progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, block_num * block_size * 100 / total_size)
                    if block_num % 10 == 0:  # 减少输出频率
                        print(f"\r  下载进度: {percent:.1f}%", end='')

            urllib.request.urlretrieve(pdf_url, filepath, reporthook=progress)
            
            print() # 换行
            
            # 检查文件大小
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"  ✓ 下载完成！文件大小: {file_size / 1024:.1f} KB")
                return True
            else:
                print(f"  ✗ 下载失败: 文件未创建")
                return False

        except Exception as e:
            print(f"  ✗ 下载失败: {e}")
            return False

    def download_part(self, start_page, end_page, part_num, title):
        """
        下载指定页码范围的部分

        Args:
            start_page: 起始页码
            end_page: 结束页码
            part_num: 部分编号
            title: 书籍标题

        Returns:
            bool: 是否下载成功
        """
        print(f"\n正在下载第{part_num}部分 ({start_page}-{end_page}页)...")

        # 打开印刷对话框
        if not self.open_print_dialog():
            return False

        # 设置页码范围
        if not self.set_page_range(start_page, end_page):
            return False

        # 再次确认页码范围是否设置成功
        time.sleep(1)
        # print("  确认页码范围设置...")
        
        # 开始印刷（点击"印刷用ファイルを開く"）
        if not self.start_print(part_num):
            return False

        # 等待PDF生成完成
        pdf_link_text = self.wait_pdf_generated(timeout=120)  # 增加超时时间
        if not pdf_link_text:
            return False

        # 打开PDF页面
        pdf_url = self.open_pdf_page()
        if not pdf_url:
            return False

        # 直接下载PDF
        return self.download_pdf_directly(pdf_url, part_num, title)

    def merge_pdf_parts(self, title, total_parts):
        """
        合并多个PDF部分为一个完整的PDF文件

        Args:
            title: 书籍标题
            total_parts: 总部分数

        Returns:
            str: 合并后的PDF文件路径，失败返回None
        """
        try:
            # 首先尝试查找不带后缀的目录
            book_dir = os.path.join(self.download_dir, title)
            
            # 如果不存在，尝试查找旧版带 .pdf 后缀的目录（兼顾旧数据）
            # 注意：如果存在带 .pdf 的目录，为避免最终文件重名冲突，我们需要稍后处理
            is_old_format = False
            if not os.path.exists(book_dir):
                old_book_dir = os.path.join(self.download_dir, f"{title}.pdf")
                if os.path.exists(old_book_dir):
                    book_dir = old_book_dir
                    is_old_format = True
            
            # 收集所有部分PDF文件
            # ... pdf_files logic ...
            
            # 尝试查找所有分段文件
            part_files = {} # map part_num -> filepath
            
            if not os.path.exists(book_dir):
                print(f"  ✗ 目录不存在: {book_dir}")
                return None
            
            # 遍历目录找符合 pattern 的文件
            # 注意：如果目录里有不同ID的同名部分，可能会有冲突，但我们假设一次只下载一本书
            for filename in os.listdir(book_dir):
                if filename.endswith('.pdf') and not filename.startswith('merged_'):
                    # 排除掉可能的最终目标文件（如果在同一目录下）
                    if filename == f"{title}.pdf":
                        continue
                        
                    match = re.search(r'_(\d{4})\.pdf$', filename)
                    if match:
                        p_num = int(match.group(1))
                        part_files[p_num] = os.path.join(book_dir, filename)

            # ... check missing parts ...

            # 如果是旧格式的目录（xxx.pdf/），我们需要先将其重命名为 xxx/
            # 否则合并后的文件 xxx.pdf 无法创建
            if is_old_format:
                new_book_dir = os.path.join(self.download_dir, title)
                try:
                    # 确保目标目录不存在
                    if not os.path.exists(new_book_dir):
                        os.rename(book_dir, new_book_dir)
                        book_dir = new_book_dir
                        print(f"  ⚠ 检测到旧版目录格式，已重命名为: {book_dir}")
                        
                        # 更新 part_files 中的路径
                        for p_num in part_files:
                            part_files[p_num] = os.path.join(book_dir, os.path.basename(part_files[p_num]))
                    else:
                        print(f"  ⚠ 目标目录已存在，无法重命名旧目录，可能会导致合并失败")
                except Exception as e:
                    print(f"  ✗ 重命名目录失败: {e}")

            # 检查是否所有部分都存在
            missing_parts = []
            for i in range(1, total_parts + 1):
                if i not in part_files:
                    missing_parts.append(i)
            
            if missing_parts:
                print(f"  ✗ 缺少部分文件，无法合并: {missing_parts}")
                print(f"  请尝试重新运行下载程序，它会自动下载缺少的部分")
                return None

            print(f"\n  开始合并PDF文件（共{total_parts}个部分）...")

            # 创建PDF写入器
            writer = PdfWriter()

            # 按顺序添加
            for i in range(1, total_parts + 1):
                pdf_file = part_files[i]
                print(f"  添加: {os.path.basename(pdf_file)}")
                try:
                    # 使用 PyPDF2.PdfReader 读取，并显式处理解密
                    # 注意：不使用 with open，而是直接传路径或手动管理
                    reader = __import__('PyPDF2').PdfReader(pdf_file)
                    
                    if reader.is_encrypted:
                        try:
                            reader.decrypt('')
                        except:
                            pass
                            
                    writer.append(reader)
                    
                except Exception as e:
                    print(f"  ✗ 读取PDF失败 {pdf_file}: {e}")
                    import traceback
                    traceback.print_exc()
                    return None

            # 这里的逻辑是：
            # 1. 现在下载的目录通常是 downloads/Title (文件夹)
            # 2. 我们最终要保存为 downloads/Title.pdf (文件)
            # 3. 它们可以共存，所以直接覆盖之前的逻辑（temp file 重命名逻辑虽然安全，但也可以简化）
            
            merged_filename = f"{title}.pdf"
            merged_filepath = os.path.join(self.download_dir, merged_filename)

            # 写入合并后的PDF
            try:
                # 确保目标文件不是文件夹（如果碰巧有人建了个同名文件夹）
                if os.path.isdir(merged_filepath):
                     print(f"  ✗ 目标位置已被占用为文件夹: {merged_filepath}")
                     return None
                     
                with open(merged_filepath, 'wb') as f:
                    writer.write(f)
            except Exception as e:
                print(f"  ✗ 写入合并PDF失败: {e}")
                import traceback
                traceback.print_exc()
                return None
            
            # 检查合并后的文件大小
            merged_size = os.path.getsize(merged_filepath)
            print(f"  ✓ 合并完成！文件大小: {merged_size / 1024:.1f} KB")

            # 删除原始部分文件和目录
            print(f"\n  删除原始部分文件...")
            try:
                # 再次确认文件未被占用
                import gc
                gc.collect()
                time.sleep(1)
                
                shutil.rmtree(book_dir)
                print(f"  ✓ 已删除临时目录: {book_dir}")
            except Exception as e:
                print(f"  ✗ 删除临时目录失败: {e}")
                # 即使删除失败，文件也已经生成成功了
                
            print(f"  ✓ 最终文件: {merged_filepath}")
            return merged_filepath

        except Exception as e:
            print(f"  ✗ 合并PDF失败: {e}")
            return None

    def can_merge_pdf_parts(self):
        """检查PDF合并所需依赖是否可用"""
        try:
            from Crypto.Cipher import AES
            _ = AES
            return True
        except Exception:
            print("\n  ⚠ 当前环境缺少PDF加密解析依赖，暂时跳过自动合并")
            return False

    def download_book(self, url, max_pages_per_part=100):
        """
        下载整本书

        Args:
            url: 书籍页面URL
            max_pages_per_part: 每部分最多页数，默认100
        """
        print("="*60)
        print(f"处理任务: {url}")

        # 检查历史记录
        history_record = self.history.get(url, {})
        if history_record.get('completed', False):
            print(f"✓ 该书籍已在历史记录中标记为完成: {history_record.get('title')}")
            # 检查文件是否确实存在
            # 这是一个简单的检查，如果文件丢了但记录完成了，可能需要手动干预
            return True

        # 获取书籍信息
        try:
            book_info = self.get_book_info(url)
        except Exception as e:
             print(f"✗ 获取书籍信息失败: {e}")
             return False

        if book_info['total_pages'] == 0:
            print("✗ 无法获取书籍页数，请检查页面")
            return False

        total_pages = book_info['total_pages']
        title = book_info['title']

        # 更新历史记录的基本信息
        self.update_history(url, title=title, total_pages=total_pages)

        # 计算需要分几部分下载
        num_parts = (total_pages + max_pages_per_part - 1) // max_pages_per_part
        print(f"书籍: {title}")
        print(f"总页数: {total_pages}, 分{num_parts}部分下载")

        # 获取已下载的部分
        downloaded_parts = history_record.get('downloaded_parts', [])

        # 分段下载
        success_count = 0
        for i in range(num_parts):
            part_num = i + 1
            
            # 检查是否已下载
            if part_num in downloaded_parts:
                print(f"✓ 第{part_num}部分已在历史记录中，跳过")
                success_count += 1
                continue

            start_page = i * max_pages_per_part + 1
            end_page = min((i + 1) * max_pages_per_part, total_pages)

            if self.download_part(start_page, end_page, part_num, title):
                success_count += 1
                # 成功后立即更新历史记录
                self.update_history(url, part_num=part_num)
            else:
                print(f"✗ 第{part_num}部分下载失败")

            # 部分之间等待
            if i < num_parts - 1 and part_num not in downloaded_parts:
                # 只有刚下载完才需要等待，如果是跳过的不用等
                print(f"  等待随机延时...")
                time.sleep(3)

        print("\n" + "="*60)
        print(f"下载进度: {success_count}/{num_parts}")
        
        # 如果所有部分都下载成功，则合并PDF
        if success_count == num_parts:
            # 检查是否能合并
            if self.can_merge_pdf_parts():
                print(f"\n开始合并PDF文件...")
                merged_file = self.merge_pdf_parts(title, num_parts)
                if merged_file:
                    print(f"\n✓ 最终文件: {merged_file}")
                    # 标记为已完成
                    self.update_history(url, completed=True)
                    return True
            else:
                print("跳过合并，已保留分段文件")
                return True
        else:
            print("⚠ 下载未全部完成，下次运行将自动断点续传")
            return False

    def close(self):
        """关闭浏览器连接"""
        if self.browser:
            print("保持浏览器连接，不关闭浏览器")


def main():
    """主函数"""
    print("日本国立国会图书馆自动下载器 v2.0")
    print("已启用: 批量下载 | 断点续传 | 进度保存")
    print("="*60)
    print("请确保已启动Chrome浏览器并开启调试端口9222")
    print("="*60)

    downloader = NDLAutoDownloader()
    if not downloader.connect_browser():
        return

    urls = []
    
    # 1. 尝试从命令行参数读取 (拖拽文件)
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if os.path.exists(input_path):
            print(f"正在读取文件: {input_path}")
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except Exception as e:
                print(f"读取文件失败: {e}")
    
    # 2. 尝试读取同目录下 urls.txt
    if not urls:
        default_list = os.path.join(get_application_path(), 'urls.txt')
        if os.path.exists(default_list):
            print(f"发现默认列表文件: urls.txt")
            reply = input("是否读取 urls.txt 进行批量下载? (y/n): ").strip().lower()
            if reply == 'y':
                with open(default_list, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    # 3. 交互式输入
    if not urls:
        print("\n请输入书籍详情页URL:")
        print("  - 输入单条链接然后回车")
        print("  - 或者输入 'f' 然后回车来选择一个文件")
        print("  - 或者直接拖入一个包含链接的txt文件")
        print("  - 输入 'q' 结束")
        
        while True:
            user_input = input("\n请选择 > ").strip()
            
            if user_input.lower() == 'q':
                break
            
            if user_input.lower() == 'f' or (os.path.isfile(user_input) and user_input.endswith('.txt')):
                # 文件模式
                file_path = user_input
                if user_input.lower() == 'f':
                    file_path = input("请输入文件路径: ").strip()
                
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            new_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                            urls.extend(new_urls)
                            print(f"已添加 {len(new_urls)} 个任务")
                            break
                    except Exception as e:
                        print(f"读取文件失败: {e}")
                else:
                    print("文件不存在")
            elif user_input:
                # 认为是URL
                urls.append(user_input)
                break

    if not urls:
        print("未提供下载任务，退出。")
        return

    print(f"\n共 {len(urls)} 个任务待处理")
    
    for i, url in enumerate(urls):
        print(f"\n>>> 开始处理第 {i+1}/{len(urls)} 个任务")
        try:
            downloader.download_book(url)
        except Exception as e:
            print(f"!!! 处理任务出错: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(urls) - 1:
            print("等待 5 秒后处理下一个任务...")
            time.sleep(5)

    print("\n" + "="*60)
    print("所有任务处理完毕")
    input("按回车键退出...")

if __name__ == "__main__":
    main()
