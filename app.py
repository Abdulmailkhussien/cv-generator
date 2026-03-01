"""
CV Generator - Multi-Template Version (v2.0)
Uses ReportLab directly for PDF generation with proper Arabic support
9 ATS-Friendly Templates with Certifications, Languages, and Projects
"""

from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import arabic_reshaper
from bidi.algorithm import get_display
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Security: Rate Limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)

# ============ FONT SETUP ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, 'fonts')

# 1. Prefer System Arial (Windows)
SYSTEM_ARIAL = r"C:\Windows\Fonts\arial.ttf"
SYSTEM_ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

if os.path.exists(SYSTEM_ARIAL):
    FONT_PATH = SYSTEM_ARIAL
    FONT_PATH_BOLD = SYSTEM_ARIAL_BOLD
    print("[OK] Using System Arial Font (Windows default)")
else:
    options = [
        ('Arimo-Regular.ttf', 'Arimo-Bold.ttf'),
        ('Tajawal-Regular.ttf', 'Tajawal-Bold.ttf'),
        ('Cairo-Regular.ttf', 'Cairo-Bold.ttf')
    ]
    
    FONT_PATH = None
    
    for reg, bold in options:
        p_reg = os.path.join(FONT_DIR, reg)
        p_bold = os.path.join(FONT_DIR, bold)
        if os.path.exists(p_reg):
            FONT_PATH = p_reg
            FONT_PATH_BOLD = p_bold
            print(f"[OK] Using bundled font: {reg}")
            break
            
    if not FONT_PATH:
        print("[WARN] No suitable fonts found! Arabic may not render correctly.")
        FONT_PATH = os.path.join(FONT_DIR, 'Cairo-Regular.ttf')
        FONT_PATH_BOLD = os.path.join(FONT_DIR, 'Cairo-Bold.ttf')

try:
    pdfmetrics.registerFont(TTFont('MainFont', FONT_PATH))
    pdfmetrics.registerFont(TTFont('MainFontBold', FONT_PATH_BOLD))
    print(f"[OK] Registered MainFont: {FONT_PATH}")
except Exception as e:
    print(f"[ERROR] Font registration failed: {e}")


# ============ TEMPLATE CONFIGURATIONS ============
TEMPLATES = {
    'classic': {
        'name_en': 'Classic',
        'name_ar': 'كلاسيكي',
        'desc_en': 'Black & White',
        'desc_ar': 'أبيض وأسود',
        'primary': HexColor('#000000'),
        'secondary': HexColor('#333333'),
        'accent': HexColor('#f0f0f0'),
        'line_color': HexColor('#000000'),
        'layout': 'standard',
        'color_preview': '#000000',
    },
    'modern': {
        'name_en': 'Modern',
        'name_ar': 'عصري',
        'desc_en': 'Blue Theme',
        'desc_ar': 'أزرق',
        'primary': HexColor('#2563eb'),
        'secondary': HexColor('#1e40af'),
        'accent': HexColor('#dbeafe'),
        'line_color': HexColor('#2563eb'),
        'layout': 'standard',
        'color_preview': '#2563eb',
    },
    'minimal': {
        'name_en': 'Minimal',
        'name_ar': 'بسيط',
        'desc_en': 'Green Theme',
        'desc_ar': 'أخضر',
        'primary': HexColor('#059669'),
        'secondary': HexColor('#047857'),
        'accent': HexColor('#d1fae5'),
        'line_color': HexColor('#059669'),
        'layout': 'standard',
        'color_preview': '#059669',
    },
    'executive': {
        'name_en': 'Executive',
        'name_ar': 'تنفيذي',
        'desc_en': 'Purple Header',
        'desc_ar': 'رأس بنفسجي',
        'primary': HexColor('#7c3aed'),
        'secondary': HexColor('#5b21b6'),
        'accent': HexColor('#ede9fe'),
        'line_color': HexColor('#7c3aed'),
        'layout': 'executive',
        'color_preview': '#7c3aed',
    },
    'compact': {
        'name_en': 'Compact',
        'name_ar': 'مضغوط',
        'desc_en': 'Orange Accent',
        'desc_ar': 'برتقالي',
        'primary': HexColor('#ea580c'),
        'secondary': HexColor('#c2410c'),
        'accent': HexColor('#ffedd5'),
        'line_color': HexColor('#ea580c'),
        'layout': 'compact',
        'color_preview': '#ea580c',
    },
    'professional': {
        'name_en': 'Professional',
        'name_ar': 'احترافي',
        'desc_en': 'Navy Sidebar',
        'desc_ar': 'شريط بحري',
        'primary': HexColor('#1e3a5f'),
        'secondary': HexColor('#2c5282'),
        'accent': HexColor('#e2e8f0'),
        'line_color': HexColor('#1e3a5f'),
        'layout': 'professional',
        'color_preview': '#1e3a5f',
    },
    'creative': {
        'name_en': 'Creative',
        'name_ar': 'إبداعي',
        'desc_en': 'Teal & Coral',
        'desc_ar': 'أزرق مخضر',
        'primary': HexColor('#0d9488'),
        'secondary': HexColor('#115e59'),
        'accent': HexColor('#ccfbf1'),
        'accent2': HexColor('#f97316'),
        'line_color': HexColor('#0d9488'),
        'layout': 'creative',
        'color_preview': '#0d9488',
    },
    'diamond': {
        'name_en': 'Diamond',
        'name_ar': 'الماسي',
        'desc_en': 'Gold Elegant',
        'desc_ar': 'ذهبي أنيق',
        'primary': HexColor('#374151'),
        'secondary': HexColor('#4b5563'),
        'accent': HexColor('#f9fafb'),
        'accent2': HexColor('#d4a843'),
        'line_color': HexColor('#d4a843'),
        'layout': 'diamond',
        'color_preview': '#d4a843',
    },
    'tech': {
        'name_en': 'Tech',
        'name_ar': 'تقني',
        'desc_en': 'Cyan Digital',
        'desc_ar': 'رقمي سماوي',
        'primary': HexColor('#475569'),
        'secondary': HexColor('#334155'),
        'accent': HexColor('#f1f5f9'),
        'accent2': HexColor('#06b6d4'),
        'line_color': HexColor('#06b6d4'),
        'layout': 'tech',
        'color_preview': '#06b6d4',
    },
}


def process_arabic(text):
    """Process Arabic text for proper display in PDF."""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text


def draw_cv_pdf(data, language='en', template='classic'):
    """Generate CV PDF using ReportLab canvas."""
    buffer = BytesIO()
    
    page_width, page_height = A4
    margin = 20 * mm
    bottom_margin = 20 * mm

    c = canvas.Canvas(buffer, pagesize=A4)
    
    is_rtl = language == 'ar'
    theme = TEMPLATES.get(template, TEMPLATES['classic'])
    
    def t(text):
        if is_rtl and text:
            return process_arabic(str(text))
        return str(text) if text else ""
    
    y = page_height - margin
    layout = theme.get('layout', 'standard')
    
    # ========== PAGE BREAK HELPER ==========
    def check_page_break(needed=15*mm):
        nonlocal y
        if y < bottom_margin + needed:
            c.showPage()
            y = page_height - margin
            return True
        return False

    # ========== ICON DRAWING FUNCTIONS ==========
    def draw_email_icon(x, y_pos, size=3*mm):
        c.saveState()
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.5)
        c.rect(x, y_pos - size*0.6, size*1.5, size*0.8, stroke=1, fill=0)
        c.line(x, y_pos + size*0.2, x + size*0.75, y_pos - size*0.3)
        c.line(x + size*1.5, y_pos + size*0.2, x + size*0.75, y_pos - size*0.3)
        c.restoreState()
        return size*1.5 + 2*mm
    
    def draw_phone_icon(x, y_pos, size=3*mm):
        c.saveState()
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.5)
        c.roundRect(x, y_pos - size*0.5, size*0.6, size, size*0.1, stroke=1, fill=0)
        c.rect(x + size*0.1, y_pos - size*0.3, size*0.4, size*0.6, stroke=0, fill=1)
        c.restoreState()
        return size*0.6 + 2*mm
    
    def draw_location_icon(x, y_pos, size=3*mm):
        c.saveState()
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.5)
        c.line(x + size*0.3, y_pos - size*0.6, x + size*0.5, y_pos - size)
        c.line(x + size*0.7, y_pos - size*0.6, x + size*0.5, y_pos - size)
        c.circle(x + size*0.5, y_pos - size*0.3, size*0.35, stroke=1, fill=0)
        c.restoreState()
        return size + 2*mm
    
    def draw_linkedin_icon(x, y_pos, size=3*mm):
        c.saveState()
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.5)
        c.ellipse(x, y_pos - size*0.4, x + size*0.8, y_pos + size*0.2, stroke=1, fill=0)
        c.ellipse(x + size*0.4, y_pos - size*0.4, x + size*1.2, y_pos + size*0.2, stroke=1, fill=0)
        c.restoreState()
        return size*1.2 + 2*mm


    # ========== HEADER - Style per layout ==========
    if layout == 'executive':
        # Full-width colored header box
        c.setFillColor(theme['primary'])
        c.rect(0, page_height - 45*mm, page_width, 45*mm, fill=True, stroke=False)
        c.setFillColorRGB(1, 1, 1)
        c.setFont('MainFontBold', 28)
        name = t(data.get('full_name', ''))
        name_width = c.stringWidth(name, 'MainFontBold', 28)
        c.drawString((page_width - name_width) / 2, y - 5*mm, name)
        y -= 15 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 14)
            title_width = c.stringWidth(job_title, 'MainFont', 14)
            c.drawString((page_width - title_width) / 2, y, job_title)
        y = page_height - 50*mm
        c.setFillColorRGB(0, 0, 0)
        
    elif layout == 'compact':
        # Left accent bar
        c.setFillColor(theme['primary'])
        c.rect(margin - 5*mm, y - 15*mm, 3*mm, 20*mm, fill=True, stroke=False)
        c.setFillColor(theme['primary'])
        c.setFont('MainFontBold', 20)
        name = t(data.get('full_name', ''))
        if is_rtl:
            c.drawRightString(page_width - margin, y, name)
        else:
            c.drawString(margin, y, name)
        y -= 7 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 11)
            c.setFillColor(theme['secondary'])
            if is_rtl:
                c.drawRightString(page_width - margin, y, job_title)
            else:
                c.drawString(margin, y, job_title)
        y -= 8 * mm
        c.setFillColorRGB(0, 0, 0)

    elif layout == 'professional':
        # Navy left stripe + right-aligned contact
        c.setFillColor(theme['primary'])
        c.rect(0, page_height - 42*mm, 8*mm, 42*mm, fill=True, stroke=False)
        # Top bar
        c.setFillColor(theme['accent'])
        c.rect(8*mm, page_height - 42*mm, page_width - 8*mm, 42*mm, fill=True, stroke=False)
        
        c.setFillColor(theme['primary'])
        c.setFont('MainFontBold', 24)
        name = t(data.get('full_name', ''))
        if is_rtl:
            c.drawRightString(page_width - margin, y - 2*mm, name)
        else:
            c.drawString(margin + 2*mm, y - 2*mm, name)
        y -= 12 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 13)
            c.setFillColor(theme['secondary'])
            if is_rtl:
                c.drawRightString(page_width - margin, y, job_title)
            else:
                c.drawString(margin + 2*mm, y, job_title)
        y = page_height - 47*mm
        c.setFillColorRGB(0, 0, 0)

    elif layout == 'creative':
        # Bold gradient-like header with accent stripe
        c.setFillColor(theme['primary'])
        c.rect(0, page_height - 40*mm, page_width, 40*mm, fill=True, stroke=False)
        # Coral accent bar at bottom of header
        accent2 = theme.get('accent2', theme['primary'])
        c.setFillColor(accent2)
        c.rect(0, page_height - 43*mm, page_width, 3*mm, fill=True, stroke=False)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont('MainFontBold', 26)
        name = t(data.get('full_name', ''))
        name_width = c.stringWidth(name, 'MainFontBold', 26)
        c.drawString((page_width - name_width) / 2, y - 3*mm, name)
        y -= 13 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 13)
            c.setFillColorRGB(0.9, 0.9, 0.9)
            title_width = c.stringWidth(job_title, 'MainFont', 13)
            c.drawString((page_width - title_width) / 2, y, job_title)
        y = page_height - 48*mm
        c.setFillColorRGB(0, 0, 0)

    elif layout == 'diamond':
        # Elegant charcoal header with gold line
        c.setFillColor(theme['primary'])
        c.rect(0, page_height - 38*mm, page_width, 38*mm, fill=True, stroke=False)
        # Gold line at bottom
        gold = theme.get('accent2', theme['line_color'])
        c.setStrokeColor(gold)
        c.setLineWidth(2)
        c.line(margin, page_height - 39*mm, page_width - margin, page_height - 39*mm)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont('MainFontBold', 26)
        name = t(data.get('full_name', ''))
        name_width = c.stringWidth(name, 'MainFontBold', 26)
        c.drawString((page_width - name_width) / 2, y - 2*mm, name)
        y -= 12 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 12)
            c.setFillColor(gold)
            title_width = c.stringWidth(job_title, 'MainFont', 12)
            c.drawString((page_width - title_width) / 2, y, job_title)
        y = page_height - 44*mm
        c.setFillColorRGB(0, 0, 0)

    elif layout == 'tech':
        # Slate header with cyan accent line
        c.setFillColor(theme['primary'])
        c.rect(0, page_height - 36*mm, page_width, 36*mm, fill=True, stroke=False)
        # Cyan line
        cyan = theme.get('accent2', theme['line_color'])
        c.setStrokeColor(cyan)
        c.setLineWidth(3)
        c.line(0, page_height - 37*mm, page_width, page_height - 37*mm)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont('MainFontBold', 22)
        name = t(data.get('full_name', ''))
        # Code-bracket style: < Name />
        display_name = name
        if not is_rtl:
            display_name = f"< {name} />"
        name_width = c.stringWidth(display_name, 'MainFontBold', 22)
        c.drawString((page_width - name_width) / 2, y - 2*mm, display_name)
        y -= 11 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 11)
            c.setFillColor(cyan)
            title_width = c.stringWidth(job_title, 'MainFont', 11)
            c.drawString((page_width - title_width) / 2, y, job_title)
        y = page_height - 42*mm
        c.setFillColorRGB(0, 0, 0)
        
    else:
        # Standard layout (classic, modern, minimal)
        if template in ['modern', 'minimal']:
            c.setFillColor(theme['accent'])
            c.rect(0, page_height - 50*mm, page_width, 50*mm, fill=True, stroke=False)
            c.setFillColor(theme['primary'])
        else:
            c.setFillColor(theme['primary'])
        
        c.setFont('MainFontBold', 22)
        name = t(data.get('full_name', ''))
        if is_rtl:
            c.drawRightString(page_width - margin, y, name)
        else:
            c.drawString(margin, y, name)
        y -= 8 * mm
        
        job_title = t(data.get('job_title', ''))
        if job_title:
            c.setFont('MainFont', 12)
            c.setFillColor(theme['secondary'])
            if is_rtl:
                c.drawRightString(page_width - margin, y, job_title)
            else:
                c.drawString(margin, y, job_title)
            y -= 6 * mm
    
    # ========== CONTACT INFO ==========
    c.setFillColorRGB(0, 0, 0)
    c.setFont('MainFont', 9)
    
    spacing = 4 * mm
    contact_data = []
    if data.get('email'):
        contact_data.append(('email', data['email']))
    if data.get('phone'):
        contact_data.append(('phone', t(data['phone'])))
    if data.get('location'):
        contact_data.append(('location', t(data['location'])))
    if data.get('linkedin'):
        contact_data.append(('linkedin', data['linkedin']))
    
    if is_rtl:
        x_pos = page_width - margin
        for icon_type, text in contact_data:
            text_width = c.stringWidth(text, 'MainFont', 9)
            x_pos -= text_width
            c.drawString(x_pos, y, text)
            x_pos -= 1*mm
            icon_width = 4*mm
            x_pos -= icon_width
            if icon_type == 'email':
                draw_email_icon(x_pos, y + 1*mm)
            elif icon_type == 'phone':
                draw_phone_icon(x_pos, y + 1*mm)
            elif icon_type == 'location':
                draw_location_icon(x_pos, y + 1*mm)
            elif icon_type == 'linkedin':
                draw_linkedin_icon(x_pos, y + 1*mm)
            x_pos -= spacing
    else:
        x_pos = margin
        for icon_type, text in contact_data:
            if icon_type == 'email':
                icon_width = draw_email_icon(x_pos, y + 1*mm)
            elif icon_type == 'phone':
                icon_width = draw_phone_icon(x_pos, y + 1*mm)
            elif icon_type == 'location':
                icon_width = draw_location_icon(x_pos, y + 1*mm)
            elif icon_type == 'linkedin':
                icon_width = draw_linkedin_icon(x_pos, y + 1*mm)
            else:
                icon_width = 0
            x_pos += icon_width
            c.drawString(x_pos, y, text)
            x_pos += c.stringWidth(text, 'MainFont', 9) + spacing
    
    y -= 5 * mm
    
    # Separator line
    c.setStrokeColor(theme['line_color'])
    c.setLineWidth(2 if template != 'classic' else 1)
    c.line(margin, y, page_width - margin, y)
    y -= 8 * mm
    
    # ========== HELPER FUNCTIONS ==========
    
    def draw_section_title(title):
        nonlocal y
        check_page_break(20*mm)
        c.setFont('MainFontBold', 12)
        c.setFillColor(theme['primary'])
        
        if template == 'modern':
            c.setFillColor(theme['accent'])
            c.rect(margin - 2*mm, y - 2*mm, page_width - 2*margin + 4*mm, 7*mm, fill=True, stroke=False)
            c.setFillColor(theme['primary'])
        elif layout == 'diamond':
            # Diamond bullet before title
            gold = theme.get('accent2', theme['line_color'])
            c.setFillColor(gold)
            diamond_text = "◆ "
            c.setFont('MainFontBold', 10)
            if is_rtl:
                c.drawRightString(page_width - margin, y, t(title))
                c.drawRightString(page_width - margin + 4*mm + c.stringWidth(t(title), 'MainFontBold', 10), y, diamond_text)
            else:
                c.drawString(margin, y, diamond_text)
                c.setFont('MainFontBold', 12)
                c.setFillColor(theme['primary'])
                c.drawString(margin + 5*mm, y, title)
        elif layout == 'tech':
            # Bracket style: [ SECTION ]
            cyan = theme.get('accent2', theme['line_color'])
            c.setFillColor(cyan)
            bracket_title = f"[ {title} ]" if not is_rtl else t(title)
            c.drawString(margin, y, bracket_title) if not is_rtl else c.drawRightString(page_width - margin, y, bracket_title)
        elif layout == 'creative':
            # Underlined section title with coral accent
            accent2 = theme.get('accent2', theme['primary'])
            if is_rtl:
                c.drawRightString(page_width - margin, y, t(title))
            else:
                c.drawString(margin, y, title)
            c.setStrokeColor(accent2)
            c.setLineWidth(2)
            c.line(margin, y - 3*mm, margin + 40*mm, y - 3*mm)
        
        if layout not in ['diamond', 'tech', 'creative']:
            if is_rtl:
                c.drawRightString(page_width - margin, y, t(title))
            else:
                c.drawString(margin, y, title)
        
        if template in ['classic', 'minimal', 'professional']:
            y_line = y - 2*mm
            c.setStrokeColor(theme['line_color'])
            c.setLineWidth(0.5)
            c.line(margin, y_line, page_width - margin, y_line)
        
        y -= 8 * mm
        c.setFillColorRGB(0, 0, 0)
    
    def wrap_text(text, font_name='MainFont', font_size=9):
        nonlocal y
        if not text:
            return
        
        c.setFont(font_name, font_size)
        text_width = page_width - 2 * margin
        processed = t(text)
        
        paragraphs = processed.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        for para in paragraphs:
            if not para.strip():
                y -= 3 * mm
                continue
            
            words = para.split()
            if not words:
                continue
                
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if c.stringWidth(test_line, font_name, font_size) < text_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                check_page_break()
                if is_rtl:
                    c.drawRightString(page_width - margin, y, line)
                else:
                    c.drawString(margin, y, line)
                y -= 4 * mm
    
    # ========== CONTENT SECTIONS ==========
    
    # Summary
    summary = data.get('summary', '')
    if summary:
        title = 'الملخص المهني' if is_rtl else 'Professional Summary'
        draw_section_title(title)
        wrap_text(summary, 'MainFont', 10)
        y -= 3 * mm
    
    # Experience
    experiences = data.get('experiences', [])
    if experiences and any(exp.get('company') for exp in experiences):
        title = 'الخبرة العملية' if is_rtl else 'Professional Experience'
        draw_section_title(title)
        
        for exp in experiences:
            if exp.get('company'):
                check_page_break(25*mm)
                c.setFont('MainFontBold', 10)
                title_text = t(exp.get('title', ''))
                dates = f"{t(exp.get('start_date', ''))} - {t(exp.get('end_date', ''))}"
                
                if is_rtl:
                    c.drawRightString(page_width - margin, y, title_text)
                    c.setFont('MainFont', 9)
                    c.drawString(margin, y, dates)
                else:
                    c.drawString(margin, y, title_text)
                    c.setFont('MainFont', 9)
                    c.drawRightString(page_width - margin, y, dates)
                y -= 5 * mm
                
                c.setFont('MainFont', 10)
                c.setFillColor(theme['secondary'])
                company = t(exp.get('company', ''))
                if is_rtl:
                    c.drawRightString(page_width - margin, y, company)
                else:
                    c.drawString(margin, y, company)
                c.setFillColorRGB(0, 0, 0)
                y -= 5 * mm
                
                desc = exp.get('description', '')
                if desc:
                    wrap_text(desc)
                
                y -= 3 * mm
    
    # Education
    education = data.get('education', [])
    if education and any(edu.get('school') for edu in education):
        title = 'التعليم' if is_rtl else 'Education'
        draw_section_title(title)
        
        for edu in education:
            if edu.get('school'):
                check_page_break(20*mm)
                c.setFont('MainFontBold', 10)
                degree = t(edu.get('degree', ''))
                year = t(edu.get('year', ''))
                
                if is_rtl:
                    c.drawRightString(page_width - margin, y, degree)
                    c.setFont('MainFont', 9)
                    c.drawString(margin, y, year)
                else:
                    c.drawString(margin, y, degree)
                    c.setFont('MainFont', 9)
                    c.drawRightString(page_width - margin, y, year)
                y -= 5 * mm
                
                c.setFont('MainFont', 10)
                c.setFillColor(theme['secondary'])
                school = t(edu.get('school', ''))
                if is_rtl:
                    c.drawRightString(page_width - margin, y, school)
                else:
                    c.drawString(margin, y, school)
                c.setFillColorRGB(0, 0, 0)
                y -= 5 * mm
                
                if edu.get('field'):
                    field = t(edu.get('field', ''))
                    if is_rtl:
                        c.drawRightString(page_width - margin, y, field)
                    else:
                        c.drawString(margin, y, field)
                    y -= 5 * mm
                
                y -= 3 * mm
    
    # Skills
    skills = data.get('skills', '')
    if skills:
        title = 'المهارات' if is_rtl else 'Skills'
        draw_section_title(title)
        
        if layout == 'creative':
            # Display skills as inline tags
            c.setFont('MainFont', 9)
            skill_list = [s.strip() for s in skills.replace('\n', ',').split(',') if s.strip()]
            x_pos = margin if not is_rtl else page_width - margin
            for skill in skill_list:
                skill_text = t(skill) if is_rtl else skill
                sw = c.stringWidth(skill_text, 'MainFont', 9)
                tag_w = sw + 6*mm
                
                if not is_rtl and x_pos + tag_w > page_width - margin:
                    y -= 7*mm
                    x_pos = margin
                    check_page_break()
                elif is_rtl and x_pos - tag_w < margin:
                    y -= 7*mm
                    x_pos = page_width - margin
                    check_page_break()
                
                # Tag background
                accent2 = theme.get('accent2', theme['primary'])
                c.setFillColor(theme['accent'])
                if is_rtl:
                    c.roundRect(x_pos - tag_w, y - 1.5*mm, tag_w, 5.5*mm, 2*mm, fill=True, stroke=False)
                    c.setFillColor(theme['primary'])
                    c.drawRightString(x_pos - 3*mm, y, skill_text)
                    x_pos -= tag_w + 2*mm
                else:
                    c.roundRect(x_pos, y - 1.5*mm, tag_w, 5.5*mm, 2*mm, fill=True, stroke=False)
                    c.setFillColor(theme['primary'])
                    c.drawString(x_pos + 3*mm, y, skill_text)
                    x_pos += tag_w + 2*mm
            y -= 5*mm
        else:
            wrap_text(skills, 'MainFont', 10)
        y -= 3 * mm
    
    # ========== NEW SECTIONS ==========
    
    # Certifications
    certifications = data.get('certifications', [])
    if certifications and any(cert.get('name') for cert in certifications):
        title = 'الشهادات' if is_rtl else 'Certifications'
        draw_section_title(title)
        
        for cert in certifications:
            if cert.get('name'):
                check_page_break(15*mm)
                c.setFont('MainFontBold', 10)
                cert_name = t(cert.get('name', ''))
                cert_year = t(cert.get('year', ''))
                
                if is_rtl:
                    c.drawRightString(page_width - margin, y, cert_name)
                    if cert_year:
                        c.setFont('MainFont', 9)
                        c.drawString(margin, y, cert_year)
                else:
                    c.drawString(margin, y, cert_name)
                    if cert_year:
                        c.setFont('MainFont', 9)
                        c.drawRightString(page_width - margin, y, cert_year)
                y -= 5 * mm
                
                issuer = cert.get('issuer', '')
                if issuer:
                    c.setFont('MainFont', 9)
                    c.setFillColor(theme['secondary'])
                    issuer_text = t(issuer)
                    if is_rtl:
                        c.drawRightString(page_width - margin, y, issuer_text)
                    else:
                        c.drawString(margin, y, issuer_text)
                    c.setFillColorRGB(0, 0, 0)
                    y -= 5 * mm
                
                y -= 2 * mm
    
    # Languages
    languages = data.get('languages', [])
    if languages and any(lng.get('language') for lng in languages):
        title = 'اللغات' if is_rtl else 'Languages'
        draw_section_title(title)
        
        for lng in languages:
            if lng.get('language'):
                check_page_break(10*mm)
                c.setFont('MainFont', 10)
                lang_name = t(lng.get('language', ''))
                level = t(lng.get('level', ''))
                
                display = f"{lang_name}  —  {level}" if level else lang_name
                if is_rtl:
                    display = f"{level}  —  {lang_name}" if level else lang_name
                
                if is_rtl:
                    c.drawRightString(page_width - margin, y, display)
                else:
                    c.drawString(margin, y, display)
                y -= 5 * mm
        y -= 2 * mm
    
    # Projects
    projects = data.get('projects', [])
    if projects and any(proj.get('name') for proj in projects):
        title = 'المشاريع' if is_rtl else 'Projects'
        draw_section_title(title)
        
        for proj in projects:
            if proj.get('name'):
                check_page_break(18*mm)
                c.setFont('MainFontBold', 10)
                proj_name = t(proj.get('name', ''))
                
                if is_rtl:
                    c.drawRightString(page_width - margin, y, proj_name)
                else:
                    c.drawString(margin, y, proj_name)
                y -= 5 * mm
                
                link = proj.get('link', '')
                if link:
                    c.setFont('MainFont', 8)
                    c.setFillColor(theme.get('accent2', theme['primary']))
                    if is_rtl:
                        c.drawRightString(page_width - margin, y, link)
                    else:
                        c.drawString(margin, y, link)
                    c.setFillColorRGB(0, 0, 0)
                    y -= 4 * mm
                
                desc = proj.get('description', '')
                if desc:
                    wrap_text(desc)
                
                y -= 3 * mm
    
    c.save()
    buffer.seek(0)
    return buffer


@app.route('/')
def index():
    return render_template('index.html', templates=TEMPLATES)


@app.route('/generate', methods=['POST'])
def generate_cv():
    try:
        data = request.json
        language = data.get('language', 'en')
        template = data.get('template', 'classic')
        
        pdf_buffer = draw_cv_pdf(data, language, template)
        
        name = data.get('full_name', 'cv').replace(' ', '_').replace('/', '-')
        filename = f"{name}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1000)
