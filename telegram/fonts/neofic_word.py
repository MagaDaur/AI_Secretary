import datetime
import docx
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches
import win32com.client
import os


password="12345"
isPassword=True

doc=Document()

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

par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(16)
par1.add_run("ТЕМА ВСТРЕЧИ").bold=True
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(14)
par1.add_run("ПРОТОКОЛ ВСТРЕЧИ")
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(12)
par1.add_run("ДАТА:        ").bold=True
par1.add_run(cur)
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(12)
par1.add_run("ВРЕМЯ:        ").bold=True
par1.add_run(str(date.hour)+":"+str(date.minute))
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(12)
par1.add_run("ДЛИТЕЛЬНОСТЬ:        ").bold=True
par1.add_run(dur)
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(12)
par1.add_run("УЧАСТНИКИ:        ").bold=True
par1.add_run(members)
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(14)
par1.add_run("ПОВЕСТКА ДНЯ")
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(14)
par1.add_run("Цель встречи:").bold=True
par1.add_run(goal)
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
for i in resume:
    par1=doc.add_paragraph()
    run = par1.add_run()
    font = run.font
    font.name = 'Arial'  # Указываем имя шрифта
    font.size = Pt(12)
    par1.add_run(i)
    par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
par1=doc.add_paragraph()
run = par1.add_run()
font = run.font
font.name = 'Arial'  # Указываем имя шрифта
font.size = Pt(14)
par1.add_run("РЕЗЮМЕ ОБСУЖДЕНИЙ")
par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
for i in resume:
    par1=doc.add_paragraph()
    run = par1.add_run()
    font = run.font
    font.name = 'Arial'  # Указываем имя шрифта
    font.size = Pt(12)
    par1.add_run(i)
    par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for j in resume[i]:
        par1=doc.add_paragraph()
        run = par1.add_run()
        font = run.font
        font.name = 'Arial'  # Указываем имя шрифта
        font.size = Pt(12)
        par1.add_run(j+")")
        par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for k in resume[i][j]:
            if k=="speakers":
                par1=doc.add_paragraph()
                run = par1.add_run()
                font = run.font
                font.name = 'Arial'  # Указываем имя шрифта
                font.size = Pt(12)
                par1.add_run(word(k)+', '.join(resume[i][j][k]))
                par1.alignment=WD_ALIGN_PARAGRAPH.LEFT
            else:
                par1=doc.add_paragraph()
                run = par1.add_run()
                font = run.font
                font.name = 'Arial'  # Указываем имя шрифта
                font.size = Pt(12)
                par1.add_run(word(k)+resume[i][j][k])
                par1.alignment=WD_ALIGN_PARAGRAPH.LEFT


    


doc.save('nonofic_prot.docx')
if isPassword:
    word = win32com.client.Dispatch('Word.Application')
    text=os.getcwd()
    text=text+"\\"
    doc = word.Documents.Open(text+'nonofic_prot.docx')
    doc.Password = password
    doc.Save()
    word.Quit()