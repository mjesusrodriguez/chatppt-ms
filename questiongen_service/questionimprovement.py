import openai
from common.openai_config import setup_openai

model_engine = setup_openai()

#Crea una pregunta, con ChatGPT
def createQuestionGPT(slot, domain):
    messages = [
        {
            "role": "user",
            "content": "You are a task oriented chatbot specialized in the " + domain +" domain. Create a coloquial question to request this slot: " + slot + " to the user. Do not include greetings or salutations in the question."
        }
    ]

    # Crear la solicitud de ChatCompletion
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # Puedes usar "gpt-4" si tienes acceso
        messages=messages,
        temperature=0.8,
        max_tokens=64,
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0
    )

    # Extraer la respuesta generada por el modelo
    generated_text = response.choices[0].message.content
    print(generated_text)

    # Eliminar comillas simples o dobles de la respuesta
    final_response = generated_text.replace('"', '').replace("'", "")
    print("Final response without quotes:", final_response)

    return final_response