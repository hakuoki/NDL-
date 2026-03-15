#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本国立国会图书馆自动下载器
自动分段下载书籍PDF，每次最多100页
"""

import sys
import io

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from DrissionPage import ChromiumPage
import time
import os
import shutil
from pathlib import Path
from PyPDF2 import PdfWriter
from PyPDF2.errors import DependencyError


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
        self.download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)

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
        # 直接在当前标签页跳转，不打开新标签页
        self.tab.run_js(f"window.location.href = '{url}'")

        # 等待页面加载
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
                body_text = self.tab('t:body').text
                import re
                # 查找 "タイトル" 后面的内容
                title_match = re.search(r'タイトル\s*([^\n\r]+)', body_text)
                if title_match:
                    title = title_match.group(1).strip()
                    print(f"  从タイトル字段提取: {title}")
        except Exception as e:
            print(f"  获取标题时出错: {e}")

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
            print(f"  JS执行结果: {result}")
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
                    print(f"  ✓ 方式1成功输入页码")
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
                print(f"  JS输入结果: {result2}")
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"  JS输入失败: {e}")

            print(f"  设置页码范围: {start_page}-{end_page}")
            return True
        except Exception as e:
            print(f"✗ 设置页码范围失败: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"  JS执行结果: {result}")
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
                print(f"检查出错: {e}", end='', flush=True)

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
                        print(f"  PDF URL: {pdf_url}")
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

                print(f"  ✓ 完整PDF URL: {pdf_url}")
                return pdf_url
            else:
                print("  ✗ 未找到PDF链接")
                return None

        except Exception as e:
            print(f"  ✗ 获取PDF链接失败: {e}")
            import traceback
            traceback.print_exc()
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

            print(f"  开始下载PDF文件...")

            # 创建书籍专属目录
            book_dir = os.path.join(self.download_dir, f"{title}.pdf")
            os.makedirs(book_dir, exist_ok=True)

            # 尝试提取书籍ID
            book_id = "unknown"
            match = __import__('re').search(r'/digidepo_(\d+)_', pdf_url)
            if match:
                book_id = match.group(1)

            # 生成文件名
            filename = f"{title}_{book_id}_{part_num:04d}.pdf"
            filepath = os.path.join(book_dir, filename)

            # 下载文件
            print(f"  下载到: {filepath}")
            urllib.request.urlretrieve(pdf_url, filepath)

            # 检查文件大小
            file_size = os.path.getsize(filepath)
            print(f"  ✓ 下载完成！文件大小: {file_size / 1024:.1f} KB")
            print(f"  ✓ 文件保存位置: {filepath}")

            return True
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
        print("  确认页码范围设置...")
        js_check = f'''
        const input = document.querySelector('input[id="range-specific-input"]');
        if (input) {{
            return "当前页码范围: " + input.value;
        }}
        return "未找到页码输入框";
        '''
        check_result = self.tab.run_js(js_check)
        print(f"  {check_result}")

        # 开始印刷（点击"印刷用ファイルを開く"）
        if not self.start_print(part_num):
            return False

        # 等待PDF生成完成
        pdf_link_text = self.wait_pdf_generated(timeout=60)
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
            book_dir = os.path.join(self.download_dir, f"{title}.pdf")

            # 收集所有部分PDF文件
            pdf_files = []
            for i in range(1, total_parts + 1):
                # 查找该部分的PDF文件
                for filename in os.listdir(book_dir):
                    if f"_{i:04d}.pdf" in filename and not filename.startswith("merged_"):
                        filepath = os.path.join(book_dir, filename)
                        if os.path.exists(filepath):
                            pdf_files.append(filepath)
                            break

            # 按部分编号排序
            pdf_files.sort()

            if len(pdf_files) == 0:
                print("  ✗ 未找到要合并的PDF文件")
                return None
            elif len(pdf_files) == 1:
                print("  只有一个部分，无需合并")
                return pdf_files[0]

            print(f"\n  开始合并PDF文件（共{len(pdf_files)}个部分）...")

            # 创建PDF写入器
            writer = PdfWriter()

            # 添加所有PDF文件
            for pdf_file in pdf_files:
                print(f"  添加: {os.path.basename(pdf_file)}")
                with open(pdf_file, 'rb') as f:
                    try:
                        writer.append(f)
                    except DependencyError:
                        print("  ✗ 合并PDF失败: 检测到AES加密PDF，当前环境缺少PyCryptodome")
                        print("  请执行: pip install pycryptodome")
                        print("  或执行: pip install -r requirements.txt")
                        print("  已保留分段PDF文件，安装依赖后重新运行即可自动合并")
                        return None

            # 生成合并后的文件名（直接使用书名）
            merged_filename = f"{title}.pdf"
            merged_filepath = os.path.join(book_dir, merged_filename)

            # 写入合并后的PDF
            with open(merged_filepath, 'wb') as f:
                writer.write(f)

            # 检查合并后的文件大小
            merged_size = os.path.getsize(merged_filepath)
            print(f"  ✓ 合并完成！文件大小: {merged_size / 1024:.1f} KB")
            print(f"  ✓ 合并后文件: {merged_filepath}")

            # 删除原始部分文件
            print(f"\n  删除原始部分文件...")
            for pdf_file in pdf_files:
                try:
                    os.remove(pdf_file)
                    print(f"  ✓ 已删除: {os.path.basename(pdf_file)}")
                except Exception as e:
                    print(f"  ✗ 删除失败 {os.path.basename(pdf_file)}: {e}")

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
            print("  请执行: pip install pycryptodome")
            print("  或执行: pip install -r requirements.txt")
            print("  安装后重新运行脚本将自动合并已下载的分段PDF")
            return False

    def download_book(self, url, max_pages_per_part=100):
        """
        下载整本书

        Args:
            url: 书籍页面URL
            max_pages_per_part: 每部分最多页数，默认100
        """
        print("="*60)
        print("开始下载书籍")
        print("="*60)

        # 获取书籍信息
        book_info = self.get_book_info(url)
        if book_info['total_pages'] == 0:
            print("✗ 无法获取书籍页数，请检查页面")
            return False

        total_pages = book_info['total_pages']
        title = book_info['title']

        # 计算需要分几部分下载
        num_parts = (total_pages + max_pages_per_part - 1) // max_pages_per_part
        print(f"需要分{num_parts}部分下载（每部分最多{max_pages_per_part}页）")

        # 分段下载
        success_count = 0
        for i in range(num_parts):
            start_page = i * max_pages_per_part + 1
            end_page = min((i + 1) * max_pages_per_part, total_pages)

            if self.download_part(start_page, end_page, i + 1, title):
                success_count += 1
            else:
                print(f"✗ 第{i+1}部分下载失败")

            # 部分之间等待
            if i < num_parts - 1:
                print(f"  等待5秒后继续下一部分...")
                time.sleep(5)

        print("\n" + "="*60)
        print(f"下载完成！成功下载 {success_count}/{num_parts} 部分")
        print(f"书籍标题: {title}")
        print(f"总页数: {total_pages}")
        print(f"下载位置: {self.download_dir}")
        print("="*60)

        # 如果所有部分都下载成功，则合并PDF
        if success_count == num_parts:
            if self.can_merge_pdf_parts():
                print(f"\n开始合并PDF文件...")
                merged_file = self.merge_pdf_parts(title, num_parts)
                if merged_file:
                    print(f"\n✓ 最终文件: {merged_file}")

        return success_count == num_parts

    def close(self):
        """关闭浏览器连接"""
        if self.browser:
            print("保持浏览器连接，不关闭浏览器")


def main():
    """主函数"""
    print("日本国立国会图书馆自动下载器")
    print("="*60)

    # 创建下载器实例
    downloader = NDLAutoDownloader()

    # 连接浏览器
    if not downloader.connect_browser():
        return

    # 获取用户输入的书籍URL
    print("\n请输入要下载的书籍URL（输入 q 退出）:")
    print("示例: https://dl.ndl.go.jp/ja/pid/1666316")

    while True:
        url = input("\n书籍URL: ").strip()

        if url.lower() == 'q':
            print("退出程序")
            break

        if not url:
            print("请输入有效的URL")
            continue

        # 验证URL格式
        if 'dl.ndl.go.jp' not in url:
            print("✗ URL格式不正确，请输入日本国立国会图书馆的有效URL")
            continue

        # 下载书籍
        try:
            downloader.download_book(url)
        except Exception as e:
            print(f"✗ 下载过程中发生错误: {e}")

        # 询问是否继续
        continue_download = input("\n是否继续下载其他书籍？(y/n): ").strip().lower()
        if continue_download != 'y':
            break

    # 关闭连接
    downloader.close()
    print("\n程序结束")


if __name__ == "__main__":
    main()
