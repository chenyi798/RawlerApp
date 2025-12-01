import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import os
from datetime import datetime

class ModernCheckbutton(ttk.Frame):
    """
    自定义复选框控件
    使用 Unicode 字符 (☑/☐) 确保百分百显示为打钩状态，
    避免不同系统主题导致的显示差异（如显示为叉）。
    """
    def __init__(self, master, text, variable, command=None, bg_color='#ffffff', **kwargs):
        super().__init__(master, **kwargs)
        self.configure(style='Card.TFrame') # 使用卡片背景色
        self.variable = variable
        self.command = command
        self.bg_color = bg_color
        
        # 颜色配置
        self.color_on = '#2980b9'   # 选中时的蓝色
        self.color_off = '#95a5a6'  # 未选中时的灰色
        self.color_hover = '#3498db'
        
        # 图标标签 (使用较大的字体显示图标)
        self.icon_label = tk.Label(self, text="☑", font=('Segoe UI Symbol', 14), 
                                   fg=self.color_on, bg=self.bg_color, bd=0, cursor="hand2")
        self.icon_label.pack(side=tk.LEFT)
        
        # 文本标签
        self.text_label = tk.Label(self, text=text, font=('Segoe UI', 10), 
                                   fg='#2c3e50', bg=self.bg_color, bd=0, cursor="hand2")
        self.text_label.pack(side=tk.LEFT, padx=(4, 0))
        
        # 绑定点击事件
        self.icon_label.bind('<Button-1>', self.toggle)
        self.text_label.bind('<Button-1>', self.toggle)
        self.bind('<Button-1>', self.toggle)
        
        # 绑定鼠标悬停效果
        for widget in [self.icon_label, self.text_label]:
            widget.bind('<Enter>', self.on_enter)
            widget.bind('<Leave>', self.on_leave)
            
        # 监听变量变化（支持外部修改变量同步UI）
        self.variable.trace_add("write", lambda *args: self.update_display())
        
        # 初始化显示
        self.update_display()
        
    def toggle(self, event=None):
        """切换状态"""
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()
            
    def update_display(self):
        """更新UI显示"""
        if self.variable.get():
            self.icon_label.config(text="☑", fg=self.color_on)
        else:
            self.icon_label.config(text="☐", fg=self.color_off)
            
    def on_enter(self, event):
        """鼠标悬停高亮"""
        if not self.variable.get():
            self.icon_label.config(fg=self.color_hover)
            
    def on_leave(self, event):
        """鼠标离开恢复"""
        if not self.variable.get():
            self.icon_label.config(fg=self.color_off)


class ModernCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数据采集助手 Pro")
        # 再次缩小窗口尺寸
        self.root.geometry("800x600")
        
        # 定义配色方案
        self.colors = {
            'bg': '#f5f7fa',           # 浅灰背景
            'primary': '#2980b9',      # 主色调蓝色
            'primary_hover': '#3498db',
            'success': '#27ae60',      # 成功绿色
            'success_hover': '#2ecc71',
            'danger': '#c0392b',       # 警告红色
            'danger_hover': '#e74c3c',
            'text': '#2c3e50',         #主要文字
            'text_light': '#7f8c8d',   # 次要文字
            'white': '#ffffff',
            'panel_bg': '#ffffff'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 尝试设置图标
        try:
            self.root.iconbitmap("crawler_icon.ico")
        except:
            pass
        
        # 数据初始化
        self.log_queue = queue.Queue()
        self.is_crawling = False
        self.current_keyword = ""
        self.current_results_dir = ""
        
        # 界面初始化
        self.setup_styles()
        self.setup_ui()
        
        # 启动日志监听
        self.update_logs()
    
    def setup_styles(self):
        """配置现代化UI样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 1. 全局配置
        style.configure('.', 
            background=self.colors['bg'], 
            foreground=self.colors['text'], 
            font=('Segoe UI', 10)
        )
        
        # 2. 容器样式
        style.configure('Card.TFrame', background=self.colors['panel_bg'])
        style.configure('Card.TLabelframe', 
            background=self.colors['panel_bg'],
            relief='flat',
            borderwidth=1
        )
        style.configure('Card.TLabelframe.Label', 
            background=self.colors['panel_bg'],
            foreground=self.colors['primary'],
            font=('Segoe UI', 11, 'bold')
        )

        # 3. 标题样式
        style.configure('Header.TLabel', 
            font=('微软雅黑', 20, 'bold'),
            background=self.colors['bg'],
            foreground=self.colors['text']
        )
        style.configure('SubHeader.TLabel', 
            font=('Segoe UI', 9),
            background=self.colors['bg'],
            foreground=self.colors['text_light']
        )

        # 4. 输入框样式
        style.configure('Modern.TEntry', 
            fieldbackground=self.colors['white'],
            borderwidth=1,
            relief='solid',
            padding=8
        )
        
        # 5. 按钮样式
        style.configure('Start.TButton',
            font=('Segoe UI', 10, 'bold'),
            background=self.colors['success'],
            foreground=self.colors['white'],
            borderwidth=0,
            padding=(20, 8),
            focuscolor='none'
        )
        style.map('Start.TButton',
            background=[('active', self.colors['success_hover']), ('disabled', '#bdc3c7')]
        )
        
        style.configure('Stop.TButton',
            font=('Segoe UI', 10, 'bold'),
            background=self.colors['danger'],
            foreground=self.colors['white'],
            borderwidth=0,
            padding=(20, 8),
            focuscolor='none'
        )
        style.map('Stop.TButton',
            background=[('active', self.colors['danger_hover']), ('disabled', '#bdc3c7')]
        )
        
        style.configure('Action.TButton',
            font=('Segoe UI', 9),
            background='#ecf0f1',
            foreground=self.colors['text'],
            borderwidth=0,
            padding=(10, 5)
        )
        style.map('Action.TButton',
            background=[('active', '#bdc3c7')]
        )

        # 6. 进度条
        style.configure('Modern.Horizontal.TProgressbar',
            troughcolor='#ecf0f1',
            background=self.colors['primary'],
            thickness=4
        )

    def setup_ui(self):
        """构建界面布局"""
        # 主内边距容器
        main_pad = ttk.Frame(self.root, style='Card.TFrame', padding=20)
        main_pad.pack(fill=tk.BOTH, expand=True)
        
        # --- 头部区域 ---
        header_frame = ttk.Frame(main_pad, style='Card.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_box = ttk.Frame(header_frame, style='Card.TFrame')
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="🕷️ 数据采集助手 Pro", style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(title_box, text="高效 · 稳定 · 多平台支持", style='SubHeader.TLabel').pack(anchor=tk.W)

        # --- 配置区域 (卡片式设计) ---
        config_frame = ttk.LabelFrame(main_pad, text=" 任务配置 ", style='Card.TLabelframe', padding=15)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Grid布局
        config_frame.columnconfigure(1, weight=1)
        
        # 关键词行
        ttk.Label(config_frame, text="搜索关键词:", font=('Segoe UI', 10, 'bold'), background=self.colors['panel_bg']).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        self.keyword_entry = ttk.Entry(config_frame, width=35, style='Modern.TEntry', font=('Segoe UI', 10))
        self.keyword_entry.grid(row=0, column=1, sticky=tk.EW)
        self.keyword_entry.bind('<Return>', lambda event: self.start_crawling())
        
        # 平台选择行 (使用自定义复选框)
        ttk.Label(config_frame, text="目标平台:", font=('Segoe UI', 10, 'bold'), background=self.colors['panel_bg']).grid(row=1, column=0, sticky=tk.W, pady=(15, 0))
        
        platform_box = ttk.Frame(config_frame, style='Card.TFrame')
        platform_box.grid(row=1, column=1, sticky=tk.W, pady=(15, 0))
        
        self.eastmoney_var = tk.BooleanVar(value=True)
        self.pbc_var = tk.BooleanVar(value=True)
        
        # 使用自定义的 ModernCheckbutton
        self.cb1 = ModernCheckbutton(platform_box, 
                                   text="东方财富网 (EastMoney)", 
                                   variable=self.eastmoney_var,
                                   bg_color=self.colors['panel_bg'],
                                   command=self.update_button_state)
        self.cb1.pack(side=tk.LEFT, padx=(0, 25))
        
        self.cb2 = ModernCheckbutton(platform_box, 
                                   text="中国人民银行 (PBC)", 
                                   variable=self.pbc_var,
                                   bg_color=self.colors['panel_bg'],
                                   command=self.update_button_state)
        self.cb2.pack(side=tk.LEFT)

        # --- 操作栏 ---
        action_frame = ttk.Frame(main_pad, style='Card.TFrame')
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 左侧主要操作
        self.start_button = ttk.Button(action_frame, text="🚀 立即开始", style='Start.TButton', command=self.start_crawling)
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_button = ttk.Button(action_frame, text="⏹ 停止任务", style='Stop.TButton', command=self.stop_crawling, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # 右侧辅助操作
        self.open_folder_button = ttk.Button(action_frame, text="📂 结果目录", style='Action.TButton', command=self.open_results_folder)
        self.open_folder_button.pack(side=tk.RIGHT)
        
        self.clear_button = ttk.Button(action_frame, text="🗑 清空日志", style='Action.TButton', command=self.clear_logs)
        self.clear_button.pack(side=tk.RIGHT, padx=(0, 10))

        # --- 状态栏 ---
        status_frame = ttk.Frame(main_pad, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.status_label = ttk.Label(status_frame, text="系统就绪", font=('Segoe UI', 9), foreground=self.colors['text_light'], background=self.colors['panel_bg'])
        self.status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', style='Modern.Horizontal.TProgressbar')
        
        # --- 日志终端区域 ---
        log_container = ttk.LabelFrame(main_pad, text=" 运行日志 ", style='Card.TLabelframe', padding=1)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # 终端风格文本框
        self.log_text = scrolledtext.ScrolledText(log_container, 
            font=('Consolas', 9),
            bg='#1e1e1e',      
            fg='#d4d4d4',      
            insertbackground='white',
            selectbackground='#264f78',
            padx=5, pady=5,
            borderwidth=0,
            highlightthickness=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # --- 底部版权 ---
        footer_label = ttk.Label(main_pad, text="v2.2 | 自动保存结果", 
            font=('Segoe UI', 8), foreground='#bdc3c7', background=self.colors['bg'])
        footer_label.pack(anchor=tk.E, pady=(5, 0))

        # 初始化焦点
        self.keyword_entry.focus_set()

    # --- 逻辑功能函数 (保持原有的核心逻辑) ---
    
    def update_button_state(self):
        if self.eastmoney_var.get() or self.pbc_var.get():
            self.start_button.state(['!disabled'])
        else:
            self.start_button.state(['disabled'])

    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            msg_content = f"[{timestamp}] [ERR] {message}\n"
            tag = "error"
        elif level == "WARNING":
            msg_content = f"[{timestamp}] [WRN] {message}\n"
            tag = "warning"
        elif level == "SUCCESS":
            msg_content = f"[{timestamp}] [OK]  {message}\n"
            tag = "success"
        else:
            msg_content = f"[{timestamp}] [INF] {message}\n"
            tag = "info"
            
        self.log_queue.put((msg_content, tag))

    def update_logs(self):
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message, tag)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self.update_logs)

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("日志已清空")

    def start_crawling(self):
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索关键词")
            self.keyword_entry.focus_set()
            return
        
        if not self.eastmoney_var.get() and not self.pbc_var.get():
            messagebox.showwarning("提示", "请至少勾选一个平台")
            return
            
        self.current_keyword = keyword
        self.is_crawling = True
        self.current_results_dir = f"Result_{self.clean_filename(keyword)}_{int(time.time())}"
        
        if not os.path.exists(self.current_results_dir):
            os.makedirs(self.current_results_dir)
            
        # UI 更新
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.keyword_entry.config(state=tk.DISABLED)
        
        # 显示进度条
        self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.progress.start(15)
        self.status_label.config(text=f"正在运行: {keyword}", foreground=self.colors['primary'])
        
        self.log_message(f"任务启动 - 关键词: {keyword}", "SUCCESS")
        
        # 线程启动
        crawler_thread = threading.Thread(target=self.run_crawlers, daemon=True)
        crawler_thread.start()

    def stop_crawling(self):
        self.is_crawling = False
        self.log_message("正在请求停止...", "WARNING")
        self.status_label.config(text="正在停止...", foreground=self.colors['danger'])

    def run_crawlers(self):
        """运行实际的爬虫任务"""
        try:
            start_time = time.time()
            success_count = 0
            total_platforms = 0
            
            # 东方财富爬取
            if self.eastmoney_var.get() and self.is_crawling:
                total_platforms += 1
                eastmoney_dir = os.path.join(self.current_results_dir, "东方财富")
                if not os.path.exists(eastmoney_dir):
                    os.makedirs(eastmoney_dir)
                
                if self.run_eastmoney_crawler(eastmoney_dir):
                    success_count += 1
            
            # 中国人民银行爬取
            if self.pbc_var.get() and self.is_crawling:
                total_platforms += 1
                pbc_dir = os.path.join(self.current_results_dir, "中国人民银行")
                if not os.path.exists(pbc_dir):
                    os.makedirs(pbc_dir)
                
                if self.run_pbc_crawler(pbc_dir):
                    success_count += 1
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            if self.is_crawling:
                self.log_message("=" * 60)
                self.log_message(f"所有爬取任务完成！总耗时: {elapsed_time:.1f}秒", "SUCCESS")
                self.log_message(f"成功平台: {success_count}/{total_platforms}")
                self.log_message(f"结果保存在: {self.current_results_dir}")
                self.log_message("=" * 60)
                self.status_label.config(text="爬取完成", foreground=self.colors['success'])
            else:
                self.log_message("爬取已由用户停止", "WARNING")
                self.status_label.config(text="已停止", foreground=self.colors['danger'])
                
        except Exception as e:
            self.log_message(f"爬取过程中发生错误: {str(e)}", "ERROR")
            self.status_label.config(text="发生错误", foreground=self.colors['danger'])
        
        finally:
            # 恢复UI状态
            self.root.after(0, self.reset_ui)

    def run_eastmoney_crawler(self, save_dir):
        """运行东方财富爬虫"""
        try:
            self.log_message("开始爬取东方财富...")
            
            # 导入东方财富爬虫
            from eastmoney_crawler import EastMoneyCrawler
            
            # 创建爬虫实例
            crawler = EastMoneyCrawler(log_callback=self.log_message)
            
            # 运行爬虫
            results = crawler.crawl_keyword(self.current_keyword, save_dir)
            
            if results and len(results) > 0:
                success_count = len([r for r in results if r.get('success', False)])
                doc_count = len([r for r in results if r.get('doc_path')])
                self.log_message(f"东方财富爬取完成: 成功 {success_count}/{len(results)} 篇, 保存 {doc_count} 个文档", "SUCCESS")
                return True
            else:
                self.log_message("东方财富未找到相关文章", "WARNING")
                return False
            
        except Exception as e:
            self.log_message(f"东方财富爬取错误: {str(e)}", "ERROR")
            return False

    def run_pbc_crawler(self, save_dir):
        """运行中国人民银行爬虫"""
        try:
            self.log_message("开始爬取中国人民银行...")
            
            # 导入中国人民银行爬虫
            from pbc_crawler import PBCCrawler
            
            # 创建爬虫实例
            crawler = PBCCrawler(log_callback=self.log_message)
            
            # 运行爬虫
            success = crawler.crawl_keyword(self.current_keyword, save_dir)
            
            if success:
                self.log_message("中国人民银行爬取完成", "SUCCESS")
                return True
            else:
                self.log_message("中国人民银行爬取失败", "ERROR")
                return False
            
        except Exception as e:
            self.log_message(f"中国人民银行爬取错误: {str(e)}", "ERROR")
            return False

    def reset_ui(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.keyword_entry.config(state=tk.NORMAL)
        self.progress.stop()
        self.progress.pack_forget() # 隐藏进度条
        self.status_label.config(text="系统就绪", foreground=self.colors['text_light'])
        self.is_crawling = False
        self.update_button_state()

    def open_results_folder(self):
        if hasattr(self, 'current_results_dir') and os.path.exists(self.current_results_dir):
            try:
                os.startfile(self.current_results_dir)
            except:
                messagebox.showinfo("提示", f"路径: {self.current_results_dir}")
        else:
            messagebox.showinfo("提示", "暂无结果文件夹")

    def clean_filename(self, filename):
        import re
        return re.sub(r'[<>:"/\\|?*]', '', filename)

def main():
    root = tk.Tk()
    
    # 颜色配置 (Log部分)
    app = ModernCrawlerGUI(root)
    app.log_text.tag_config("error", foreground="#e74c3c")   # 鲜红
    app.log_text.tag_config("warning", foreground="#f1c40f") # 金黄
    app.log_text.tag_config("success", foreground="#2ecc71") # 亮绿
    app.log_text.tag_config("info", foreground="#3498db")    # 亮蓝
    
    # 居中显示
    root.update_idletasks()
    width = 800
    height = 600
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    root.mainloop()

if __name__ == "__main__":
    main()