from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template(
    "{question} {context}"
)


class Prompt:
    def __init__(self, llm_instructions, context, question):
        self.llm_instructions = llm_instructions
        self.context = context
        self.question = question
        self.prompt = prompt_template.format(context=context, question=question)


PROMPTS = [
    {
        "llm_instructions": "Ты — умный, внимательный и ответственный русскоязычный автоматический ассистент. " \
                            "Ты досканально анализируешь служебные переговоры и отвечаешь на вопросы по их содержанию. От этого зависит моя работа.",
        "question": """
                    Сейчас тебе будет предоставлен протокол служебных переговоров.
                    Твоей задачей является выделить основной вопрос в обсуждении и смежную информацию: 
                    
                    Вопрос обсуждения - основная тема обсуждения, которую ты должен выявить в ходе анализа 
                    Принятое решение - решение, которое было принято, по вопросу обсуждения, которое ты должен выявить в ходе анализа 
                    Участники обсуждения - Список людей, участвовавших в этом обсуждении, которое ты должен выявить в ходе анализа 
                    Контекст обсуждения - пара наиболее важных отрывков обсуждения вопроса
                    Время - время, в которое обсуждался опрос
                    
                    Вывод должен быть в только формате json файла состоящего из списка словарей, никаких лишних сток, примеры формата ответа: 
                    [{'Вопрос обсуждения': 'Целесообразность высаживания клумб в центре',
                    'Принятое решение': 'Высадить цветочные клумбы в центре',
                    'Участники обсуждения': ['Гордеев А.И,', 'Шавлуков Д.Д.'],
                    'Контекст обсуждения': 'полный контекст обсуждения по достигнутому решению.',
                    'Время': '10:37'},
                    {{'Вопрос обсуждения': 'Предпосылки к увеличению суммы прожиточного минимума',
                    'Принятое решение': 'Увеличить сумму прожиточного минимума',
                    'Участники обсуждения': ['Габриелян Е.Е,', 'Гордеев А.И,',],
                    'Контекст обсуждения': 'полный контекст обсуждения по достигнутому решению.',
                    'Время': '15:52'}]
                    "Далее представлены служебные переговоры для анализа: """,
    },

    {
        "llm_instructions": "Ты — умный, внимательный и ответственный русскоязычный автоматический ассистент. ",
        "question":
            """
            Сейчас тебе будет предоставлен протокол служебных переговоров.
            Твоей задачей является выделить весь перечень поручений в переговорах, а именно название поручения, то, что нужно сделать по итогу поручения, имя человека, которому это нужно сделать и срок, до которого нужно выполнить поручение
            Вернуть ответ нужно в формате json файла состоящего из списка словарей в виде строки, без каких либо дополнительных пояснений и форматирования текста.
            Пример структуры json файла:
            [
                {
                    "Название поручения": "...",
                    "Описание поручения": "...",
                    "Имя исполнителя": "...",
                    "Срок": "..."
                }
            ]
            Если ты не можешь выделить поручение, то без дополнительных пояснений выведи пустой список на языке python
            Далее представлены служебные переговоры для анализа: 
            """,
    },
]
