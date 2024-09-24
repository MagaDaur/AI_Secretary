from fpdf import FPDF
import datetime
import PyPDF2
from local_lib import get_chat_metadata
import logging

logging.basicConfig(level=logging.INFO)

months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
voc = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
        6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
        11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
        16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX"}


def generate_protocol(data, theme="Тема совещания", count_of_members=3):
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "./fonts/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "./fonts/DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font('DejaVu', "B", 12)

    line_height = pdf.font_size * 2.5
    
    date=datetime.datetime.now()
    cur=str(date.day)+"."+str(date.month)+"."+str(date.year)

    resume = data['transcribed_text']

    # Заголовок протокола
    pdf.cell(200, 10, txt="ПРОТОКОЛ", ln=1, align="C")
    pdf.cell(200, 10, txt="совещания по теме " + theme, ln=1, align="C")
    pdf.set_line_width(1)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, 30, 200, 30)
    pdf.cell(200, 10, txt="Москва", ln=1, align="C")
    pdf.cell(170, 10, txt="от " + cur + " №", ln=1, align="R")
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(180, 47, 200, 47)
    pdf.set_font('DejaVu', "", 12)
    pdf.cell(200, 10, txt="Присутствовали:", ln=1, align="L")

    # Заполнение списка участников (пустыми строками)
    for _ in range(count_of_members):
        pdf.cell(200, 10, txt="", ln=1, align="L")

    pdf.set_line_width(1)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, 60 + line_height * count_of_members, 200, 60 + line_height * count_of_members)

    k = 1

    logging.info(resume)
    
    for item in resume:
        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 10, txt=voc[k] + ".     " + item['Вопрос обсуждения'], ln=1, align="C")
        pdf.cell(200, 10, txt="(" + ", ".join(item['Участники обсуждения']) + ")", ln=1, align="C")

        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 10, txt=str(1) + ".     " + item['Принятое решение'], ln=1, align="L")

        pdf.set_text_color(173, 216, 230)
        context = "Контекст обсуждения: " + item['Контекст обсуждения']
        left_part, right_part = context.split(":", 1)
        left_part = left_part + ":"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, left_part, ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, right_part)

        context = "Время: " + item['Время']
        left_part, right_part = context.split(":", 1)
        left_part = left_part + ":"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, left_part, ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, right_part)

        k += 1

    # Добавление страницы с перечнем поручений (пример, можно добавить реальные поручения)
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.cell(170, 10, txt="№", ln=1, align="R")
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(180, 18, 200, 18)
    pdf.cell(200, 10, txt=f"{date.day} {months[date.month - 1]} {date.year} г.", ln=1, align="R")
    pdf.set_font('DejaVu', "B", 12)
    pdf.cell(200, 10, txt="ПЕРЕЧЕНЬ ПОРУЧЕНИЙ", ln=1, align="C")
    pdf.cell(200, 10, txt="по итогам совещания по теме " + theme, ln=1, align="C")
    pdf.set_font('DejaVu', "", 12)

    # Пример добавления поручений
    pdf.multi_cell(200, 10, txt="1. Организация-исполнитель 1 (И. О. Фамилия руководителя)", align="L")
    pdf.multi_cell(0, line_height)
    pdf.cell(200, 10, txt="Сделать то-то.", ln=1, align="L")
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Срок - до 1 сентября 2024", ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 10, "")

    metadata = get_chat_metadata(data['chat_id'])
    filename = ''.join(data["file_name"].split(".")[:-1])
    pdf_filepath = f'./temp/{data["chat_id"]}/{filename}.pdf'

    pdf.output(pdf_filepath)
    if 'password' in metadata:
        with open(pdf_filepath, 'r+b') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pdf_writer = PyPDF2.PdfWriter()
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            pdf_writer.encrypt(user_password=metadata['password'], owner_pwd=metadata['password'])
            
            pdf_writer.write(pdf_file)
    
    return pdf_filepath
