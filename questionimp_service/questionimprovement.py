import openai
from common.openai_config import setup_openai

model_engine = setup_openai()

#Mejora la pregunta realizada, con ChatGPT
def improveQuestionchatGPT(question, domain):
    # manejar el prompt para que devuelva un json con parámetros faltantes.
    #prompt = "Give me only one alternative question for this one in the scope of restaurant booking: " + question

    messages = [
        {
            "role": "user",
            "content": f"Given the original question: '{question}' in the context of the '{domain}' domain, rephrase this question into a more conversational, polite, and natural tone. Ensure the new question still elicits the same specific information from the customer. Provide only one alternative question that maintains clarity and fits the domain’s context."
        }
    ]

    # Crear la solicitud de ChatCompletion
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  #Puedes usar "gpt-4" si tienes acceso
        messages=messages,
        temperature=0.8,
        max_tokens=128,
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0
    )

    # Extraer la respuesta generada por el modelo
    generated_text = response.choices[0].message.content
    print(generated_text)

    final_response = response.choices[0].message.content

    if not final_response:
        final_response = question

    return final_response