from fpdf import FPDF
import datetime
import PyPDF2


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

pdf=FPDF()
pdf.add_page()

password="12345"
isPassword=True

pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
pdf.set_font('DejaVu', "B", 12)

line_height = pdf.font_size * 2.5
theme="такой-то"
goal="декларация цели встречи"
date=datetime.datetime.now()
cur=str(date.day)+"."+str(date.month)+"."+str(date.year)
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
           'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
count_of_members=3
count_of_questions=2
dur="00:15"
members="Петр, Игорь, Марина, Семён"
voc={1:"I",2:"II",3:"III",4:"IV",5:"V",
     6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",
     11:"XI",12:"XII",13:"XIII",14:"XIV",15:"XV",
     16:"XVI",17:"XVII",18:"XVIII",19:"XIX",20:"XX"}
resume={
    "I.    Название вопроса 1: ":{
        "a":{
            "speakers":["Имя 1", "Имя 2"],
            "decision":"Решили утвердить то-то",
            "date": "01.01.2025",
            "otv":"Имя",
            "obraz":"Описание образа результата",
            "context":"краткий контекст обсуждения по достигнутому решению.",
            "time":"мм:сс"
        },
        "b":{
            "speakers":["Имя"],
            "decision":"Сняли развилку по вопросу такому-то.",
            "context":"краткий контекст обсуждения по достигнутому решению.",
            "time":"мм:сс"
        }
    },
    "II.     Название вопроса 2: ":{
        "a":{
            "speakers":["Имя"],
            "decision":"Не пришли к согласию по вопросу такому-то. Требуется дополнительная проработка. ",
            "context":"краткий контекст обсуждения по достигнутому решению.",
            "time":"мм:сс"
        },
        "b":{
            "speakers":["Имя"],
            "decision":"Подсветили статус вопросы. Выявили риски. Предложили такие-то решения. ",
            "context":"краткий контекст обсуждения по достигнутому решению.",
            "time":"мм:сс"
        }
    }
}

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


    



pdf.output("nonofic_prot.pdf")
if isPassword:
    with open("nonofic_prot.pdf", 'rb') as input_file:
        pdf_reader = PyPDF2.PdfReader(input_file)
        pdf_writer = PyPDF2.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        pdf_writer.encrypt(user_password=password, owner_pwd=password, use_128bit=True)
        with open("nonofic_prot.pdf", 'wb') as output_file:
            pdf_writer.write(output_file)