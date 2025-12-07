import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, KeepTogether
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import time
import re
import os
import html
import urllib3

urllib3.disable_warnings()

# 注册中文字体（Windows系统）
try:
    font_path = "C:\\Windows\\Fonts\\simhei.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SimHei', font_path))
        pdfmetrics.registerFont(TTFont('SimHei-Bold', font_path))
    else:
        font_path = "C:\\Windows\\Fonts\\msyh.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('SimHei', font_path))
            pdfmetrics.registerFont(TTFont('SimHei-Bold', font_path))
except Exception as e:
    print(f"警告: 无法加载中文字体，中文可能显示为乱码: {e}")


class Vue3PDFGenerator:
    def __init__(self):
        self.base_url = "https://cn.vuejs.org"
        self.visited = set()
        self.content = []
        self.toc_entries = []
        self.max_chars_per_section = 8000
        self.max_paragraphs_per_section = 20
        self.max_paragraph_length = 600
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def clean_text(self, text):
        """彻底清理文本 - 防止乱码"""
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('\r', '\n')
        text = re.sub(r"\t", '    ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ ]{2,}', ' ', text)
        text = ''.join(ch for ch in text if (ch == '\n' or ord(ch) >= 32))
        return text.strip()
    
    def split_text_into_paragraphs(self, text, max_length=280):
        """将长文本分割成多个段落 - 避免过多空格"""
        raw_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        paragraphs = []
        for p in raw_paragraphs:
            if max_length and len(p) > max_length:
                parts = []
                start = 0
                while start < len(p):
                    part = p[start:start+max_length]
                    if start + max_length < len(p):
                        last_space = part.rfind(' ')
                        if last_space > max_length // 2:
                            parts.append(part[:last_space])
                            start += last_space + 1
                            continue
                    parts.append(part)
                    start += max_length
                paragraphs.extend([pt.strip() for pt in parts if pt.strip()])
            else:
                paragraphs.append(p)
        return paragraphs
    
    def extract_code_blocks(self, html_content):
        """从HTML内容中提取代码块 - 按函数分割"""
        code_blocks = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for idx, code_elem in enumerate(soup.find_all('pre')):
            code_text = code_elem.get_text()
            if len(code_text.strip()) > 20:
                code_lines = code_text.strip().split('\n')
                current_block = []
                
                for line in code_lines:
                    current_block.append(line)
                    if len('\n'.join(current_block)) > 400:
                        current_block.pop()
                        break
                
                if current_block and len('\n'.join(current_block)) > 20:
                    code_blocks.append({
                        'index': idx,
                        'code': '\n'.join(current_block)[:420],
                        'tag': code_elem.name
                    })
        
        return code_blocks
    
    def get_sidebar_links(self):
        """获取左侧导航栏所有链接"""
        return self.get_full_demo_links()
    
    def get_full_demo_links(self):
        """返回仅包含文档章节的 Vue 3 官方文档链接"""
        return [
            ("开始", "#"),
            ("介绍", "/guide/introduction.html"),
            ("快速开始", "/guide/quick-start.html"),
            ("基础", "#"),
            ("创建一个应用", "/guide/essentials/application.html"),
            ("模板语法", "/guide/essentials/template-syntax.html"),
            ("响应性基础", "/guide/essentials/reactivity-fundamentals.html"),
            ("计算属性", "/guide/essentials/computed.html"),
            ("类和样式绑定", "/guide/essentials/class-and-style.html"),
            ("条件渲染", "/guide/essentials/conditional.html"),
            ("列表渲染", "/guide/essentials/list.html"),
            ("事件处理", "/guide/essentials/event-handling.html"),
            ("表单输入绑定", "/guide/essentials/forms.html"),
            ("侦听器", "/guide/essentials/watchers.html"),
            ("模板引用", "/guide/template-refs.html"),
            ("组件基础", "/guide/essentials/component-basics.html"),
            ("生命周期", "/guide/essentials/lifecycle.html"),
            ("深入组件", "#"),
            ("注册", "/guide/components/registration.html"),
            ("Props", "/guide/components/props.html"),
            ("事件", "/guide/components/events.html"),
            ("组件 v-model", "/guide/components/v-model.html"),
            ("透传 Attributes", "/guide/components/attrs.html"),
            ("插槽", "/guide/components/slots.html"),
            ("依赖注入", "/guide/components/provide-inject.html"),
            ("异步组件", "/guide/components/async-components.html"),
            ("内置组件", "#"),
            ("Transition", "/guide/built-ins/transition.html"),
            ("TransitionGroup", "/guide/built-ins/transition-group.html"),
            ("KeepAlive", "/guide/built-ins/keep-alive.html"),
            ("Teleport", "/guide/built-ins/teleport.html"),
            ("Suspense", "/guide/built-ins/suspense.html"),
            ("逻辑复用", "#"),
            ("组合式函数", "/guide/reusability/composables.html"),
            ("自定义指令", "/guide/reusability/custom-directives.html"),
            ("插件", "/guide/reusability/plugins.html"),
            ("应用规模化", "#"),
            ("单文件组件", "/guide/scaling-up/sfc.html"),
            ("工具链", "/guide/scaling-up/tooling.html"),
            ("路由", "/guide/scaling-up/routing.html"),
            ("状态管理", "/guide/scaling-up/state-management.html"),
            ("测试", "/guide/scaling-up/testing.html"),
            ("服务端渲染 (SSR)", "/guide/scaling-up/ssr.html"),
            ("最佳实践", "#"),
            ("生产部署", "/guide/best-practices/production-deployment.html"),
            ("性能优化", "/guide/best-practices/performance.html"),
            ("安全最佳实践", "/guide/best-practices/security.html"),
            ("无障碍访问", "/guide/best-practices/accessibility.html"),
            ("TypeScript", "#"),
            ("TypeScript 总览", "/guide/typescript/overview.html"),
            ("TypeScript 与选项式 API", "/guide/typescript/options-api.html"),
            ("TypeScript 与组合式 API", "/guide/typescript/composition-api.html"),
            ("进阶主题", "#"),
            ("使用 Vue 的多种方式", "/guide/extras/ways-of-using-vue.html"),      
            ("组合式 API 常见问答", "/guide/extras/composition-api-faq.html"),          
            ("深入响应式系统", "/guide/extras/reactivity-in-depth.html"),
            ("渲染机制", "/guide/extras/rendering-mechanism.html"),
            ("渲染函数 & JSX", "/guide/extras/render-function.html"),
            ("Vue 与 Web Components", "/guide/extras/web-components.html"),
            ("动画技巧", "/guide/extras/animation.html"),
        ]
    
    def fetch_page_content(self, url):
        """获取页面内容，自动处理 SSL 错误并重试"""
        if url in self.visited:
            return None, []
        self.visited.add(url)
        full_url = url if url.startswith('http') else f"{self.base_url}{url}"
        tries = 0
        while tries < 3:
            try:
                response = requests.get(full_url, headers=self.headers, timeout=10, verify=False)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.content, 'html.parser')
                
                code_blocks = self.extract_code_blocks(str(soup))
                
                main = soup.find('main') or soup.find('article')
                if main:
                    for script in main(['script', 'style']):
                        script.decompose()
                    
                    text = main.get_text(separator='\n')
                    text = self.clean_text(text)
                    
                    if len(text) > 1200:
                        text = text[:1200]
                    
                    return text, code_blocks
                
                time.sleep(0.5)
                return None, []
            except Exception as e:
                print(f"获取页面失败 {url}: 重试 {tries+1}/3")
                tries += 1
                time.sleep(1)
        print(f"获取页面失败 {url}: 已放弃")
        return None, []
    
    def create_toc(self, story, styles):
        """创建目录 - 支持分组标题"""
        toc_title = Paragraph("目 录", styles['Heading1'])
        story.append(toc_title)
        story.append(Spacer(1, 0.2 * inch))
        
        toc_style = ParagraphStyle(
            'TOC',
            parent=styles['Normal'],
            fontSize=10,
            fontName='SimHei',
            leftIndent=0.3 * inch,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        toc_group_style = ParagraphStyle(
            'TOCGroup',
            parent=styles['Normal'],
            fontSize=11,
            fontName='SimHei-Bold',
            leftIndent=0.1 * inch,
            spaceAfter=10,
            spaceBefore=8,
            textColor=HexColor('#2c3e50'),
            alignment=TA_LEFT
        )
        
        entry_number = 0
        for title, href in self.toc_entries:
            if href == "#":
                story.append(Paragraph(title, toc_group_style))
            else:
                entry_number += 1
                if entry_number > 200:
                    break
                toc_line = f"{entry_number}. {title}"
                story.append(Paragraph(toc_line, toc_style))
        
        story.append(Spacer(1, 0.3 * inch))
        story.append(PageBreak())
    
    def format_code_block(self, code_text):
        """格式化代码块 - 按函数/块分割"""
        lines = code_text.split('\n')
        display_lines = []
        line_count = 0
        
        for line in lines:
            if line_count >= 50:
                break
            stripped = line.rstrip()
            if stripped or (display_lines and not display_lines[-1]):
                display_lines.append(stripped)
                if stripped:
                    line_count += 1
        
        while display_lines and not display_lines[-1]:
            display_lines.pop()
        
        code_text = '\n'.join(display_lines)
        
        code_style = ParagraphStyle(
            'CodeBlock',
            fontName='Courier',
            fontSize=7,
            leading=10,
            leftIndent=0.15 * inch,
            rightIndent=0.15 * inch,
            backColor=HexColor('#f5f5f5'),
            textColor=HexColor('#333333'),
            borderPadding=6,
            spaceAfter=6
        )
        
        try:
            return Preformatted(code_text, code_style)
        except:
            return Paragraph("[代码块]", code_style)
    
    def generate_pdf(self, output_file="vue3_manual.pdf"):
        """生成PDF文档"""
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=0.7 * inch,
            leftMargin=0.7 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.7 * inch
        )
        story = []
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName='SimHei-Bold',
            fontSize=28,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            leading=35
        )
        
        heading2_style = ParagraphStyle(
            'SectionTitle',
            fontName='SimHei-Bold',
            fontSize=14,
            textColor=HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=12,
            leading=18,
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'NormalText',
            fontName='SimHei',
            fontSize=10,
            leading=14,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            textColor=HexColor('#333333')
        )
        
        code_title_style = ParagraphStyle(
            'CodeTitle',
            fontName='SimHei-Bold',
            fontSize=9,
            textColor=HexColor('#555555'),
            spaceAfter=6,
            spaceBefore=8,
            leading=12
        )
        
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Vue 3 完整使用手册", title_style))
        story.append(Spacer(1, 1.0 * inch))
        story.append(PageBreak())
        
        links = self.get_sidebar_links()
        self.toc_entries = links
        
        self.create_toc(story, styles)
        
        processed_count = 0
        for i, (title, url) in enumerate(links):
            if url == "#":
                continue
            
            print(f"处理 ({i+1}/{len(links)}): {title}")
            
            content, code_blocks = self.fetch_page_content(url)
            if content:
                processed_count += 1
                
                try:
                    title_clean = title.strip()
                    title_clean = ''.join(c for c in title_clean if ord(c) >= 32 or c == '\n')
                    story.append(Paragraph(title_clean[:60], heading2_style))
                except Exception as e:
                    print(f"章节标题处理失败: {e}")
                    title_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', title)
                    story.append(Paragraph(title_clean[:50], heading2_style))
                
                paragraphs = self.split_text_into_paragraphs(content)
                added_para_count = 0
                for para_text in paragraphs:
                    if added_para_count >= 8:
                        break
                    
                    para_text = para_text.strip()
                    para_text = re.sub(r' +', ' ', para_text)
                    para_text = ''.join(c for c in para_text if ord(c) >= 32 or c == '\n')
                    
                    if len(para_text) > 10:
                        try:
                            story.append(Paragraph(para_text[:500], normal_style))
                            added_para_count += 1
                        except Exception as e:
                            print(f"段落处理失败: {e}")
                            pass
                
                if code_blocks:
                    story.append(Spacer(1, 0.08 * inch))
                    code_title = f"代码示例 ({len(code_blocks)} 个)"
                    try:
                        story.append(Paragraph(code_title, code_title_style))
                    except:
                        pass
                    
                    code_added = 0
                    for code_block in code_blocks:
                        if code_added >= 100:
                            break
                        try:
                            story.append(self.format_code_block(code_block['code']))
                            code_added += 1
                        except Exception as e:
                            print(f"代码块处理失败: {e}")
                            pass
                
                story.append(Spacer(1, 0.15 * inch))
                story.append(PageBreak())
                
                time.sleep(0.6)
        
        try:
            doc.build(story)
            print(f"\nPDF已生成: {output_file}")
            print(f"已处理 {processed_count} 个页面")
            print(f"文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")
        except Exception as e:
            print(f"生成PDF失败: {e}")


if __name__ == "__main__":
    generator = Vue3PDFGenerator()
    generator.generate_pdf("./vue3_manual.pdf")
    print("完成!")
