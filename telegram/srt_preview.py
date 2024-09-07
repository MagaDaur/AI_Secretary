from fpdf import FPDF
import subtitle_parser
import re

def create_pdf(filename: str):
    pdf=FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font('DejaVu', '', 12)

    line_height = pdf.font_size * 2.5

    with open(f'./temp/{filename}/speaker.srt', 'r', encoding="utf-8") as input_file:
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
    

    pdf.output(f'{filename}.pdf')

    return f'{filename}.pdf'