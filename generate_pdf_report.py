# -*- coding: utf-8 -*-
"""生成PDF格式的系统分析报告"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_pdf_report():
    """Create PDF report with Chinese fonts"""
    
    # Register Chinese font
    font_path = r"C:\Windows\Fonts\simhei.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SimHei', font_path))
        default_font = 'SimHei'
    else:
        print("Warning: SimHei font not found, using default font")
        default_font = 'Helvetica'
    
    # Create document
    output_path = r'C:\Users\zhangmohan\Desktop\PetHospital_Project\信息系统\白之助宠物医院系统分析报告.pdf'
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    
    # Build content
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    elements.append(Paragraph('白之助宠物医院信息管理系统', title_style))
    elements.append(Paragraph('课程大作业：系统分析报告', heading_style))
    elements.append(Spacer(1, 12))
    
    # Basic info table
    info_data = [
        ['系统名称', '白之助宠物医院信息管理系统'],
        ['系统类型', '宠物医疗机构管理信息系统'],
        ['技术框架', 'FastAPI + Vue 3 + SQLAlchemy + SQLite'],
        ['开发团队', '信息系统开发组'],
        ['开发时间', '2024年']
    ]
    
    table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), default_font),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), default_font),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Management objectives
    elements.append(Paragraph('一、管理目标', heading_style))
    objectives = [
        '提高宠物医疗服务质量：通过规范化的档案管理、预约挂号、病历记录，确保诊疗过程的科学性和可追溯性',
        '优化资源配置效率：实现医生排班、笑舍分配、药品库存的智能管理，降低运营成本',
        '增强患者体验：为主人提供便捷的预约、查询、支付等自助服务',
        '支持医疗决策：通过知识图谱和AI辅助诊断，辅助医生进行科学决策',
        '建立数据基础：收集和管理宠物医疗大数据，为后续分析和研究提供支撑'
    ]
    
    for obj in objectives:
        elements.append(Paragraph('• ' + obj, styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    # System structure
    elements.append(Paragraph('二、系统结构', heading_style))
    elements.append(Paragraph('系统采用典型的三层架构模式：', styles['Normal']))
    
    arch_data = [
        ['表现层', 'Vue 3前端，为不同角色提供定制化界面'],
        ['业务逻辑层', 'FastAPI后端，包含核心业务逻辑和权限控制'],
        ['数据访问层', 'SQLAlchemy + SQLite，实现数据持久化']
    ]
    
    arch_table = Table(arch_data, colWidths=[1.5*inch, 4*inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), default_font),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(arch_table)
    
    elements.append(Spacer(1, 12))
    
    # Core modules
    elements.append(Paragraph('三、核心功能模块', heading_style))
    
    modules = [
        ('用户与权限', '基于角色的访问控制(RBAC)'),
        ('主人与宠物档案', '记录宠物主人和宠物基本信息'),
        ('预约挂号', '在线预约、医生分配、优先级管理'),
        ('就诊与病历', '详细病历记录、不可追溯修改'),
        ('处方管理', '药物治疗方案、库存冻结机制'),
        ('药品库存', '分院库存管理、安全库存预警'),
        ('住院管理', '笑舍分配、隔离策略'),
        ('护理日志', '住院患者护理记录'),
        ('收费结算', '发票管理、支付处理'),
        ('AI诊断', '知识图谱推理、人机决策审计')
    ]
    
    for module, desc in modules:
        elements.append(Paragraph(f'• {module}：{desc}', styles['Normal']))
    
    elements.append(PageBreak())
    
    # Data entities
    elements.append(Paragraph('四、数据库核心实体关系', heading_style))
    
    entity_data = [
        ['实体', '说明'],
        ['User', '系统用户（医生、护士、管理员）'],
        ['Owner', '宠物主人'],
        ['Pet', '宠物患者'],
        ['Appointment', '预约挂号记录'],
        ['MedicalRecord', '就诊病历'],
        ['Prescription', '处方药物'],
        ['Drug', '药品主数据'],
        ['CageUnit', '住院笑舍'],
        ['Invoice', '收费发票']
    ]
    
    entity_table = Table(entity_data, colWidths=[1.5*inch, 4*inch])
    entity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), default_font),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(entity_table)
    
    elements.append(Spacer(1, 12))
    
    # System boundaries
    elements.append(Paragraph('五、系统边界', heading_style))
    elements.append(Paragraph('系统范围内:', styles['Normal']))
    
    inside_items = [
        '宠物主人和档案管理',
        '预约挂号和医生排班',
        '就诊和诊疗记录',
        '处方和药品管理',
        '住院和笑舍分配',
        '收费和发票管理'
    ]
    
    for item in inside_items:
        elements.append(Paragraph('✓ ' + item, styles['Normal']))
    
    elements.append(Spacer(1, 8))
    elements.append(Paragraph('系统范围外:', styles['Normal']))
    
    outside_items = [
        '财务核算和报表',
        '医疗设备管理',
        '物资采购和供应链',
        '人力资源和薪酬',
        '医学科研管理'
    ]
    
    for item in outside_items:
        elements.append(Paragraph('✗ ' + item, styles['Normal']))
    
    elements.append(PageBreak())
    
    # Control mechanisms
    elements.append(Paragraph('六、系统控制机制', heading_style))
    
    control_sections = [
        ('访问控制', '基于角色的权限管理'),
        ('数据完整性', '病历审计、处方冻结、库存控制'),
        ('业务规则', '预约优先级、库存预警、超期处理'),
        ('系统安全', '密码策略、会话管理、操作日志、数据加密')
    ]
    
    for control, desc in control_sections:
        elements.append(Paragraph(f'• {control}：{desc}', styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    # Summary
    elements.append(Paragraph('七、总结', heading_style))
    elements.append(Paragraph(
        '本系统是一个功能完整的宠物医院信息管理系统，涵盖患者档案、预约挂号、诊疗记录、'
        '药品管理、住院照护、收费结算等核心业务。系统采用现代化的三层架构，引入AI辅助诊断，'
        '实现了数据驱动的医疗管理。通过严格的访问控制、数据完整性约束、业务规则控制，'
        '确保了诊疗质量和患者安全。系统具有良好的可扩展性和集成性。',
        styles['Normal']
    ))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph('文档版本：1.0 | 生成日期：2024年4月', styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    print(f"PDF report generated: {output_path}")

if __name__ == '__main__':
    create_pdf_report()
