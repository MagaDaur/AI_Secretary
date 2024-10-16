from fpdf import FPDF, XPos, YPos, Align
from datetime import datetime
import time
from pypdf import PdfReader, PdfWriter
import os

roman_digits = {
    1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V',
    6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X',
    11: 'XI', 12: 'XII', 13: 'XIII', 14: 'XIV', 15: 'XV',
    16: 'XVI', 17: 'XVII', 18: 'XVIII', 19: 'XIX', 20: 'XX'
}

months = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
]

def create_pdf(data: list[list[dict]], fp: str, password: str = None):
    questions = data[0]
    assignments = data[1]

    members = set()
    for question in questions:
        for member in question['Участники обсуждения']:
            members.add(member)
    members = list(members)

    pdf = FPDF()

    pdf.add_font('DejaVu', '', './fonts/DejaVuSans.ttf')
    pdf.add_font('DejaVu', 'B', './fonts/DejaVuSans-Bold.ttf')
    pdf.add_font('DejaVu', 'I', './fonts/DejaVuSans-Oblique.ttf')
    pdf.add_font('DejaVu', 'BI', './fonts/DejaVuSans-BoldOblique.ttf')

    pdf.add_page()

    pdf.set_font('DejaVu', 'B', 14)
    pdf.set_y(20)
    pdf.cell(190, 10, text='ПРОТОКОЛ СОВЕЩАНИЯ', align=Align.C, border='B', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(190, 10, text='Москва', align=Align.C, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(190, 10, text=f"от {datetime.today().strftime('%d.%m.%Y')} №______________", align=Align.R, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font('DejaVu', '', 14)
    pdf.cell(190, 10, text='Присутствовали:', align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for member in members:
        pdf.cell(190, 7, text='  ' + member, align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    for i in range(len(questions)):
        question = questions[i]

        pdf.cell(190, 10, text=f'{roman_digits[i + 1]}.    {question['Вопрос обсуждения']}.', align=Align.C, border='B', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.multi_cell(190, 10, text=f'({', '.join(question["Участники обсуждения"])})', align=Align.C, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font('DejaVu', 'I', 14)
        pdf.set_text_color(90, 90, 190)

        pdf.multi_cell(190, 10, text=f'**Контекст обсуждения:** {question['Контекст обсуждения']}.', align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT, markdown=True)
        pdf.multi_cell(190, 10, text=f'**Решение:** {question["Принятое решение"]}.', align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT, markdown=True)
        pdf.multi_cell(190, 10, text=f'**Время:** {question['Тайм-код']}', align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT, markdown=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('DejaVu', '', 14)

    pdf.add_page()

    year, mon, day, _, _, _, _, _, _ = time.localtime()

    pdf.cell(190, 10, text=f'№______________', align=Align.R, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(190, 10, text=f"{day} {months[mon + 1]} {year} г.", align=Align.R, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(190, 10, text='ПЕРЕЧЕНЬ ПОРУЧЕНИЙ', align=Align.C, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(190, 5, text='по итогам совещания', align=Align.C, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_y(pdf.get_y() + 8)

    pdf.set_font('DejaVu', '', 14)
    for i in range(len(assignments)):
        assignment = assignments[i]
        pdf.set_x(30)
        pdf.multi_cell(170, 20, text=f"{i + 1}. {assignment['Имя исполнителя']}", align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(36)
        pdf.multi_cell(170, 10, text=assignment['Описание поручения'], align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(36)
        pdf.multi_cell(170, 10, text=f"**Срок** - {assignment['Срок выполнения']}", align=Align.L, new_x=XPos.LMARGIN, new_y=YPos.NEXT, markdown=True)
    pdf.set_x(0)

    pdf.output(fp)
    
    if password:
        reader = PdfReader(fp)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.encrypt(password)

        os.remove(fp)

        with open(fp, 'wb') as out_file:
            writer.write(out_file)