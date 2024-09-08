from fpdf import FPDF
import datetime
import PyPDF2
import json

def get_metadata(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)


def set_metadata(file_path: str, value: dict):
    with open(file_path, 'w') as file:
        json.dump(value, file)


def get_chat_metadata(chat_id):
    return get_metadata(f'./temp/{chat_id}/metadata.json')



def set_chat_metadata(chat_id, value):
    set_metadata(f'./temp/{chat_id}/metadata.json', value)

def word(a:str):
    if a=="speakers":
        return "Докладчики:"
    elif a=="date":
        return "Срок:"
    elif a=="otv":
        return "Ответственный:"
    elif a=="obraz":
        return "Образ результата:"
    elif a=="context":
        return "Контекст обсуждения:"
    elif a=="time":
        return "Время:"
    else:
        return ""

theme="такой-то"
goal="декларация цели встречи"
date=datetime.datetime.now()
cur=str(date.day)+"."+str(date.month)+"."+str(date.year)
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
           'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

dur="00:15"
members="Петр, Игорь, Марина, Семён"
voc={1:"I",2:"II",3:"III",4:"IV",5:"V",
     6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",
     11:"XI",12:"XII",13:"XIII",14:"XIV",15:"XV",
     16:"XVI",17:"XVII",18:"XVIII",19:"XIX",20:"XX"}

def create_pdf(data: dict):

    llm_reply = data['transcribed_text']

    resume = {}
    for i in range(len(llm_reply)):
        for j in range(len(llm_reply[i])):
            resume[f'{voc[j]}.      {llm_reply[i][j]['Вопрос обсуждения']}'] = {
                'speakers': llm_reply[i][j]['Участники обсуждения'],
                'decision': llm_reply[i][j]['Принятое решение'],
                'context': llm_reply[i][j]['Контекст обсуждения'],
                'time': llm_reply[i][j]['Время'],
            }

    pdf=FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font('DejaVu', "B", 12)

    line_height = pdf.font_size * 2.5

    pdf.set_font('DejaVu', "B", 16)
    pdf.cell(200, 10, txt="ТЕМА ВСТРЕЧИ", ln=1, align="L")
    pdf.set_font('DejaVu', "", 14)
    pdf.cell(200, 10, txt="ПРОТОКОЛ ВСТРЕЧИ", ln=1, align="L")
    pdf.multi_cell(0, line_height)
    pdf.set_font('DejaVu', "", 12)
    pdf.cell(200, 10, txt="ДАТА:        "+cur, ln=1, align="L")
    pdf.cell(200, 10, txt="ВРЕМЯ:        "+str(date.hour)+":"+str(date.minute), ln=1, align="L")
    pdf.cell(200, 10, txt="ДЛИТЕЛЬНОСТЬ:        "+dur, ln=1, align="L")
    pdf.cell(200, 10, txt="УЧАСТНИКИ:        "+members, ln=1, align="L")
    pdf.multi_cell(0, line_height)
    pdf.set_font('DejaVu', "", 14)
    pdf.cell(200, 10, txt="ПОВЕСТКА ДНЯ", ln=1, align="L")
    pdf.multi_cell(0, line_height)
    pdf.set_font('DejaVu', "", 12)
    pdf.cell(200, 10, txt="Цель встречи:"+goal, ln=1, align="L")
    pdf.multi_cell(0, line_height)
    for i in resume:
        pdf.cell(200, 10, txt=i, ln=1, align="L")
        pdf.multi_cell(0, line_height)
    pdf.set_font('DejaVu', "", 14)
    pdf.cell(200, 10, txt="РЕЗЮМЕ ОБСУЖДЕНИЙ", ln=1, align="L")
    pdf.multi_cell(0, line_height)
    pdf.set_font('DejaVu', "", 12)
    for i in resume:
        pdf.cell(200, 10, txt=i, ln=1, align="L")
        for j in resume[i]:
            pdf.cell(200, 10, txt=j+")", ln=1, align="L")
            for k in resume[i][j]:
                if k=="speakers":
                    pdf.cell(200, 10, txt=word(k)+', '.join(resume[i][j][k]), ln=1, align="L")
                else:
                    pdf.cell(200, 10, txt=word(k)+resume[i][j][k], ln=1, align="L")


    
    metadata = get_chat_metadata(data['chat_id'])
    pdf_filepath = f'./temp/{data['chat_id']}/{''.join(data['file_name'].split('.')[:-1])}.pdf'

    pdf.output(pdf_filepath)
    if 'password' in metadata:
        with open(pdf_filepath, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            pdf_writer = PyPDF2.PdfWriter()
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            pdf_writer.encrypt(user_password=metadata['password'], owner_pwd=metadata['password'], use_128bit=True)
            with open(pdf_filepath, 'wb') as output_file:
                pdf_writer.write(output_file)
    
    return pdf_filepath