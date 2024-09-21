from fpdf import FPDF
import subtitle_parser
import re
import os
import pathlib

def create_pdf(file_path: str):
    pdf=FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "./fonts/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "./fonts/DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font('DejaVu', '', 12)

    line_height = pdf.font_size * 2.5

    with open(file_path, 'r', encoding="utf-8") as input_file:
        parser = subtitle_parser.SrtParser(input_file)
        parser.parse()

    print(parser.subtitles[0], parser.subtitles[0].start, parser.subtitles[0].end)

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

    pdf_filepath = file_path.replace('.srt', '.pdf')

    pdf.output(pdf_filepath)

    return pdf_filepath