from fpdf import FPDF
import datetime
import PyPDF2

pdf=FPDF()
pdf.add_page()

password="12345"
isPassword=True

pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
pdf.set_font('DejaVu', "B", 12)

line_height = pdf.font_size * 2.5
theme="такой-то"
date=datetime.datetime.now()
cur=str(date.day)+"."+str(date.month)+"."+str(date.year)
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
           'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
count_of_members=3
count_of_questions=2
voc={1:"I",2:"II",3:"III",4:"IV",5:"V",
     6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",
     11:"XI",12:"XII",13:"XIII",14:"XIV",15:"XV",
     16:"XVI",17:"XVII",18:"XVIII",19:"XIX",20:"XX"}
questions={
    "Название вопроса 1":{
        "speakers":["Докладчик 1", "Докладчик 2"],
        "decissions":{
            "Принятое решение 1":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            },
            "Принятое решение 2":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            }
        }
    },
    "Название вопроса 2":{
        "speakers":["Докладчик 1", "Докладчик 2", "Докладчик 3"],
        "decissions":{
            "Принятое решение 1":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            },
            "Принятое решение 2":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            },
            "Принятое решение 3":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            },
            "Принятое решение 4":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            }
        }
    },
    "Название вопроса 3":{
        "speakers":["Докладчик 1", "Докладчик 2"],
        "decissions":{
            "Принятое решение 1":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            },
            "Принятое решение 2":{
                "context":"краткий контекст обсуждения по достигнутому решению.",
                "time":"мм:сс"
            }
        }
    }
}
poruch={
    "1":{
        "ispolnitely":["Организация-исполнитель 1 (И. О. Фамилия руководителя)"],
        "todo":"Сделать то-то.",
        "date":"до 1 сентября 2024"
    },
    "2":{
        "ispolnitely":["Организация-исполнитель 1 (И. О. Фамилия руководителя)",
                       "Организация-исполнитель 2 (И. О. Фамилия руководителя)",
                       "Организация-исполнитель 3 (И. О. Фамилия руководителя)"],
        "todo":"Сделать то-то.",
        "date":"до 1 сентября 2024"
    }
}



pdf.cell(200, 10, txt="ПРОТОКОЛ", ln=1, align="C")
pdf.cell(200, 10, txt="совещания по теме "+theme, ln=1, align="C")
pdf.set_line_width(1)
pdf.set_draw_color(0, 0, 0)
pdf.line(10, 30, 200, 30)
pdf.cell(200, 10, txt="Москва", ln=1, align="C")
pdf.cell(170, 10, txt="от "+cur+ " №", ln=1, align="R")
pdf.set_line_width(0.2)
pdf.set_draw_color(0, 0, 0)
pdf.line(180, 47, 200, 47)
pdf.set_font('DejaVu', "", 12)
pdf.cell(200, 10, txt="Присутствовали:", ln=1, align="L")
for i in range(count_of_members):
    pdf.cell(200, 10, txt="", ln=1, align="L")
pdf.set_line_width(1)
pdf.set_draw_color(0, 0, 0)
pdf.line(10, 60+line_height*count_of_members, 200, 60+line_height*count_of_members)
k=1
u=1
for i in questions:
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=voc[k]+".     "+i, ln=1, align="C")
    #pdf.set_line_width(0.2)
    #pdf.set_draw_color(0, 0, 0)
    #pdf.line(10, 60+line_height*count_of_members+line_height, 200, 60+line_height*count_of_members+line_height)
    pdf.cell(200, 10, txt="("+", ".join(questions[i]["speakers"])+")", ln=1, align="C")
    u=1
    for j in questions[i]["decissions"]:
        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 10, txt=str(u)+".     "+j, ln=1, align="L")
        pdf.set_text_color(173, 216, 230)
        context="Контекст обсуждения: "+str(questions[i]["decissions"][j]["context"])
        left_part, right_part = context.split(":", 1)
        left_part=left_part+":"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, left_part, ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, right_part)
        context="Время: "+str(questions[i]["decissions"][j]["time"])
        left_part, right_part = context.split(":", 1)
        left_part=left_part+":"
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, left_part, ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, right_part)
        u+=1
    k+=1
    #pdf.set_line_width(0.2)
    #pdf.set_draw_color(0, 0, 0)
    #pdf.line(10, 60+line_height*count_of_members+line_height+u*3*line_height+2*line_height, 200, 60+line_height*count_of_members+line_height+u*3*line_height+2*line_height)
    #pdf.set_line_width(1)
    #pdf.set_draw_color(0, 0, 0)
    #pdf.line(10, 60+line_height*count_of_members+u*3*line_height+2*line_height, 200, 60+line_height*count_of_members+u*3*line_height+2*line_height)
pdf.add_page()
pdf.set_text_color(0, 0, 0)
pdf.cell(170, 10, txt="№", ln=1, align="R")
pdf.set_line_width(0.2)
pdf.set_draw_color(0, 0, 0)
pdf.line(180, 18, 200, 18)
pdf.cell(200, 10, txt=str(date.day)+" "+str(months[date.month-1])+" "+str(date.year)+" г.", ln=1, align="R")
pdf.set_font('DejaVu', "B", 12)
pdf.cell(200, 10, txt="ПЕРЕЧЕНЬ ПОРУЧЕНИЙ", ln=1, align="C")
pdf.cell(200, 10, txt="по итогам совещания по теме "+theme, ln=1, align="C")
pdf.set_font('DejaVu', "", 12)
for i in poruch:
    text=str(i)+".     "
    text+=', '.join(poruch[i]["ispolnitely"])
    pdf.multi_cell(200, 10, txt=text, align="L")
    pdf.multi_cell(0, line_height)
    pdf.cell(200, 10, txt=poruch[i]["todo"], ln=1, align="L")
    context="Срок - "+poruch[i]["date"]
    left_part, right_part = context.split("-", 1)
    right_part=right_part
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, left_part, ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 10, right_part)
    pdf.multi_cell(0, line_height)
    



pdf.output("ofic_prot.pdf")
if isPassword:
    with open("ofic_prot.pdf", 'rb') as input_file:
        pdf_reader = PyPDF2.PdfReader(input_file)
        pdf_writer = PyPDF2.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        pdf_writer.encrypt(user_password=password, owner_pwd=password, use_128bit=True)
        with open("ofic_prot.pdf", 'wb') as output_file:
            pdf_writer.write(output_file)