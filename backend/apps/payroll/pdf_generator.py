"""
PDF generation utilities for payslips.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class PayslipPDFGenerator:
    """
    Generate PDF payslips for payroll records.
    """
    
    def __init__(self, payroll_record):
        self.payroll_record = payroll_record
        self.company = payroll_record.company
        self.employee = payroll_record.employee
        self.buffer = BytesIO()
    
    def generate(self):
        """
        Generate the PDF payslip.
        
        Returns:
            BytesIO: PDF file buffer
        """
        # Create the PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
        )
        
        # Add company header
        elements.append(Paragraph(self.company.name, title_style))
        elements.append(Paragraph("PAYSLIP", heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Add payslip period
        period_text = f"Pay Period: {self.payroll_record.period_start.strftime('%B %d, %Y')} to {self.payroll_record.period_end.strftime('%B %d, %Y')}"
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Employee information table
        employee_data = [
            ['Employee Information', ''],
            ['Employee ID:', self.employee.employee_id],
            ['Name:', self.employee.full_name],
            ['Department:', self.employee.department.name],
            ['Position:', self.employee.position or 'N/A'],
        ]
        
        employee_table = Table(employee_data, colWidths=[2 * inch, 4 * inch])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(employee_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Attendance information
        attendance_data = [
            ['Attendance Information', ''],
            ['Working Days:', str(self.payroll_record.working_days)],
            ['Present Days:', str(self.payroll_record.present_days)],
            ['Leave Days:', str(self.payroll_record.leave_days)],
            ['Absent Days:', str(self.payroll_record.absent_days)],
            ['Attendance %:', f"{self.payroll_record.attendance_percentage:.2f}%"],
        ]
        
        attendance_table = Table(attendance_data, colWidths=[2 * inch, 4 * inch])
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(attendance_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Salary breakdown table
        salary_data = [
            ['Salary Component', 'Amount'],
            ['Basic Salary', f"{self.company.currency} {self.payroll_record.basic_salary:,.2f}"],
            ['Allowances', f"{self.company.currency} {self.payroll_record.allowances:,.2f}"],
            ['Gross Salary', f"{self.company.currency} {self.payroll_record.gross_salary:,.2f}"],
            ['Deductions', f"{self.company.currency} {self.payroll_record.deductions:,.2f}"],
            ['Net Salary', f"{self.company.currency} {self.payroll_record.net_salary:,.2f}"],
        ]
        
        salary_table = Table(salary_data, colWidths=[3 * inch, 3 * inch])
        salary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
        ]))
        
        elements.append(salary_table)
        elements.append(Spacer(1, 0.5 * inch))
        
        # Add footer
        footer_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(footer_text, footer_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        disclaimer_text = "This is a computer-generated payslip and does not require a signature."
        elements.append(Paragraph(disclaimer_text, footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        pdf = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf
    
    def get_filename(self):
        """
        Generate a filename for the payslip.
        
        Returns:
            str: Filename for the PDF
        """
        period = self.payroll_record.period_start.strftime('%Y-%m')
        employee_id = self.employee.employee_id
        return f"payslip_{employee_id}_{period}.pdf"


def generate_payslip_pdf(payroll_record):
    """
    Convenience function to generate a payslip PDF.
    
    Args:
        payroll_record: PayrollRecord instance
        
    Returns:
        tuple: (pdf_bytes, filename)
    """
    generator = PayslipPDFGenerator(payroll_record)
    pdf_bytes = generator.generate()
    filename = generator.get_filename()
    return pdf_bytes, filename
