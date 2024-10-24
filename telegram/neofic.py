from fpdf import FPDF, XPos, YPos, Align
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import roman

months = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
]

def create_pdf(data: list[list[dict]], fp: str, password: str = None):
    questions = data[0]
    members = set()
    duration = questions[-1]['Тайм-код'].split(' - ')[1]
    date = datetime.today().strftime('%d.%m.%Y')
    time = datetime.today().strftime('%H:%M:%S')

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

    pdf.set_font('DejaVu', '', 18)
    pdf.set_text_color(0, 9, 66)

    pdf.set_y(30)
    pdf.set_x(30)
    pdf.set_char_spacing(2)
    pdf.cell(h=20, text='ПРОТОКОЛ ВСТРЕЧИ', new_y=YPos.NEXT)
    pdf.set_char_spacing(0)

    pdf.set_text_color(0)

    pdf.set_font(style='B', size=10)
    pdf.set_x(30)
    pdf.cell(50, 10, text='ДАТА:')
    pdf.set_font(style='')
    pdf.cell(h=10, text=date, new_y=YPos.NEXT)

    pdf.set_font(style='B')
    pdf.set_x(30)
    pdf.cell(50, 10, text='ВРЕМЯ:')
    pdf.set_font(style='')
    pdf.cell(h=10, text=time, new_y=YPos.NEXT)

    pdf.set_font(style='B')
    pdf.set_x(30)
    pdf.cell(50, 10, text='ДЛИТЕЛЬНОСТЬ:')
    pdf.set_font(style='')
    pdf.cell(h=10, text=duration, new_y=YPos.NEXT)

    pdf.set_font(style='B')
    pdf.set_x(30)
    pdf.cell(50, 10, text='УЧАСТНИКИ:')
    pdf.set_font(style='')
    pdf.multi_cell(110, 10, text=', '.join(members), new_y=YPos.NEXT)
    
    pdf.set_font(style='', size=16)
    pdf.set_text_color(0, 9, 66)

    pdf.set_x(30)
    pdf.set_char_spacing(2)
    pdf.cell(h=20, text='ПОВЕСТКА ДНЯ', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_char_spacing(0)

    pdf.set_text_color(0)

    for i in range(len(questions)):
        question = questions[i]

        pdf.set_font(style='B', size=10)
        pdf.set_x(30)
        pdf.cell(20, 10, text=roman.toRoman(i + 1) + '.')

        pdf.set_font(style='')
        pdf.multi_cell(150, 10, text=question['Вопрос обсуждения'], new_y=YPos.NEXT)

    pdf.set_font('DejaVu', '', 16)
    pdf.set_text_color(0, 9, 66)

    pdf.set_x(30)
    pdf.set_char_spacing(2)
    pdf.cell(h=25, text='РЕЗЮМЕ ОБСУЖДЕНИЙ', new_y=YPos.NEXT)
    pdf.set_char_spacing(0)

    pdf.set_text_color(0)

    for i in range(len(questions)):
        question = questions[i]
        
        pdf.set_font(style='B', size=10)
        pdf.set_x(30)
        pdf.multi_cell(150, text=f'{roman.toRoman(i + 1)}.  {question['Вопрос обсуждения']}:', new_y=YPos.NEXT, max_line_height=7, padding=(3, 0))

        pdf.set_font(style='')
        pdf.set_x(40)
        pdf.multi_cell(150, 5, text=f'**Докладчики:** {', '.join(question['Участники обсуждения'])}', new_y=YPos.NEXT, markdown=True)

        pdf.set_x(40)
        pdf.multi_cell(150, 5, text=question['Принятое решение'] + '.', new_y=YPos.NEXT)

        pdf.set_font(style='I')
        pdf.set_x(40)
        pdf.set_text_color(0, 112, 193)
        pdf.multi_cell(150, text=f'**Контекст обсуждения:** {question['Контекст обсуждения']}', markdown=True, new_y=YPos.NEXT, padding=(3, 0))

        pdf.set_x(40)
        pdf.cell(text=f'**Время:** {question['Тайм-код']}', markdown=True, new_y=YPos.NEXT)

        pdf.set_text_color(0)

    pdf.output(fp)

    if password:
        reader = PdfReader(fp)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.encrypt(password)

        with open(fp, 'wb') as out_file:
            writer.write(out_file)

    