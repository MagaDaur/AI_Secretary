from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template(
    "{context} {question}"
)


class Prompt:
    def __init__(self, llm_instructions, context, question):
        self.llm_instructions = llm_instructions
        self.context = context
        self.question = question
        self.prompt = prompt_template.format(context=context, question=question)


PROMPTS = [
    {
        "llm_instructions": "Ты — русскоязычный автоматический ассистент. Ты разговариваешь с людьми и помогаешь им.",
        "question": "Посчитай сколько раз в тексте было упомянуто слово сука и выдай ответ числом!",
    },

    #
    # {
    #     "llm_instructions": "",
    #     "question": "",
    # },
]