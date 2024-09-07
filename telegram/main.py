from fpdf import FPDF
import subtitle_parser
import re
import PyPDF2

pdf=FPDF()
pdf.add_page()

password="12345"
isPassword=True

pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
pdf.set_font('DejaVu', '', 12)

line_height = pdf.font_size * 2.5

with open('output.srt', 'r', encoding="utf-8") as input_file:
    parser = subtitle_parser.SrtParser(input_file)
    parser.parse()

parser.print_warnings()
prev=""
for subtitle in parser.subtitles:
    left_part, right_part = subtitle.text.split(":", 1)
    if prev!=left_part:
        pdf.multi_cell(0, line_height)
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, left_part, ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, right_part)
        prev=left_part
    else:
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, right_part)




pdf.output("simple_demo.pdf")   
if isPassword:
    with open("simple_demo.pdf", 'rb') as input_file:
        pdf_reader = PyPDF2.PdfReader(input_file)
        pdf_writer = PyPDF2.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        pdf_writer.encrypt(user_password=password, owner_pwd=password, use_128bit=True)
        with open("simple_demo.pdf", 'wb') as output_file:
            pdf_writer.write(output_file)