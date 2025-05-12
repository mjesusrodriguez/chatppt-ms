# Imports
from bson import ObjectId
from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import json
import re
import random

from common.mongo_config import MongoDB

# Cargar variables de entorno
load_dotenv()

# Cargar URLs de microservicios desde el .env
DOMAIN_MANAGER_URL = os.getenv('DOMAIN_MANAGER_URL')
INTENT_REC_URL = os.getenv('INTENT_REC_URL')
DISC_PARAMETER_URL = os.getenv('DISC_PARAMETER_URL')
SLOT_FILLING_URL = os.getenv('SLOT_FILLING_URL')
QUESTION_GEN_URL = os.getenv('QUESTION_GEN_URL')
QUESTION_IMPROVEMENT_URL = os.getenv('QUESTION_IMPROVEMENT_URL')
OPEN_DOMAIN_URL = os.getenv('OPEN_DOMAIN_URL')
SERVICE_SELECTION_URL = os.getenv('SERVICE_SELECTION_URL')
QUESTION_RETRIEVAL_URL = os.getenv('QUESTION_RETRIEVAL_URL')
TAG_FILTER_URL = os.getenv('FILTER_URL', "http://tagfilter_service:5000/filter")
ADITIONAL_QUESTIONS_URL = os.getenv('ADITIONAL_QUESTIONS_URL')
SLOTFILLING_URL = os.getenv('SLOTFILLING_URL')
RETRIEVE_QUESTIONS_URL = os.getenv('RETRIEVE_QUESTIONS_URL')
FILTER_BY_TAGS_URL = os.getenv('FILTER_BY_TAGS_URL')
DETECT_POSITIVE_URL = os.getenv('DETECT_POSITIVE_URL')

# Inicializar Flask app
app = Flask(__name__)

# Variables globales
dialogue_history = {'useranswers': []}
goodbye_keywords = ['goodbye', 'bye', 'see you', 'later', 'farewell', 'take care', 'thanks', 'thank you', 'talk to you later', 'bye bye']
open_domain_phrases = [
    r'what do you think', r'tell me about', r'can you share', r'what is your opinion', r'explain to me'
]

# Funciones auxiliares locales
def check_for_goodbye(user_input):
    for keyword in goodbye_keywords:
        if re.search(rf'\b{keyword}\b', user_input.lower()):
            return True
    return False

def detect_open_domain(user_input):
    for phrase in open_domain_phrases:
        if re.search(phrase, user_input.lower()):
            return True
    return False

# Funciones que llaman a microservicios
def call_domain_manager(user_input):
    response = requests.post(DOMAIN_MANAGER_URL, json={"input": user_input})
    print ("[DEBUG][domain]: ", response.json().get('domains', []))
    return response.json().get('domains', [])

def call_intent_rec(user_input, domain):
    print("[DEBUG] Enviando a intent_rec:", {"input": user_input, "domain": domain})
    response = requests.post(INTENT_REC_URL, json={"input": user_input, "domain": domain})
    print ("[DEBUG][intent]: ", response.json().get('intent', []))
    return response.json().get('intent', '')

def call_slot_filling(user_input, slots, user_answers=None):
    print("[DEBUG] call_slot_filling -> user_input:", user_input)
    print("[DEBUG] call_slot_filling -> slots:", slots)
    print("[DEBUG] call_slot_filling -> useranswers:", slots)

    payload = {"input": user_input, "slots": slots}
    if user_answers:
        payload["useranswers"] = user_answers

    response = requests.post(SLOT_FILLING_URL, json=payload)
    if response.status_code == 200:
        response_json = response.json()
        raw_filled_slots = response_json.get("filled_slots")
        try:
            parsed_slots = json.loads(raw_filled_slots)
            return parsed_slots
        except json.JSONDecodeError as e:
            print("[ERROR] No se pudo parsear filled_slots:", e)
            return {}
    else:
        print("[ERROR] Slot filling falló con código:", response.status_code)
        return {}

def call_question_generation(slot, domain):
    response = requests.post(QUESTION_GEN_URL, json={"slot": slot, "domain": domain})
    return response.json().get('created_question', slot)

def call_question_improvement(question, domain):
    response = requests.post(QUESTION_IMPROVEMENT_URL, json={"question": question, "domain": domain})
    return response.json().get('improved_question', question)

def call_open_domain(user_input, user_answers):
    response = requests.post(OPEN_DOMAIN_URL, json={"input": user_input, "useranswers": user_answers})
    return response.json().get('chatbot_answer', 'I cannot help with that.')

def call_extract_slots(intent, service_id, domain):
    payload = {
        "intent": intent,
        "service_id": service_id,
        "domain": domain
    }

    try:
        response = requests.post(SLOTFILLING_URL, json=payload)
        response.raise_for_status()
        return response.json().get("slots", [])
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Fallo en llamada a /extract-slots: {e}")
        return []

def call_question_retrieval(service_id, intent, domain):
    response = requests.post(RETRIEVE_QUESTIONS_URL, json={
        "service_id": service_id,
        "intent": intent,
        "domain": domain
    })
    if response.status_code == 200:
        return response.json().get("slots", {})
    else:
        print(f"[ERROR] question_retrieval failed: {response.text}")
        return {}

def call_filter_services(data):
    print("[DEBUG][gateway -> tagfilter] data:", data)
    response = requests.post(TAG_FILTER_URL, json=data)
    return response.json()

def call_question_retrieval(service_id, intent, domain):
    response = requests.post(QUESTION_RETRIEVAL_URL, json={"service_id": service_id, "intent": intent, "domain": domain})
    return response.json()

@app.route('/')
def home():
    return render_template('chat-api.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    global dialogue_history
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    print("Datos recibidos:", data)

    user_input = data.get('userinput')
    user_answers = data.get('useranswers', [])

    if user_answers:
        dialogue_history['useranswers'] = user_answers

    # Si es final de flujo
    if data.get('final') in [True, 'true', 'True']:
        return send_data_to_server(data)

    # Si tasks ya está lleno
    if data.get('tasks'):
        return manage_task_oriented_dialogue(data)

    detected_domain = data.get('domain')
    detected_domains = data.get('detected_domains', [])

    if detected_domain == "out-of-domain" or not detected_domains:
        detected_domains = call_domain_manager(user_input)

        if isinstance(detected_domains, str):
            detected_domains = [detected_domains]

        if detect_open_domain(user_input):
            detected_domains = ['out-of-domain']

    if 'out-of-domain' in detected_domains:
        return manage_open_dialogue(data)

    # Detección de intents para los dominios detectados
    if 'tasks' not in data:
        data['tasks'] = {}

    for domain in detected_domains:
        intent = call_intent_rec(user_input, domain)
        data['tasks'][domain] = intent.lower()

    return manage_task_oriented_dialogue(data)

def manage_open_dialogue(data):
    user_input = data.get('userinput')
    user_answers = data.get('useranswers', [])
    chatbot_answer = call_open_domain(user_input, user_answers)

    user_answers.append({"user": user_input, "chatbot": chatbot_answer})

    return jsonify({
        'chatbot_answer': chatbot_answer,
        'useranswers': user_answers,
        'dom': 'out-of-domain',
    }), 200

def manage_task_oriented_dialogue(data):
    print("[DEBUG] Datos recibidos en manage_task_oriented_dialogue:", data)

    user_input = data.get('userinput')
    user_answers = data.get('useranswers', [])
    tasks = data.get('tasks', {})
    service_id = data.get('service_id')
    services = data.get('services', [])
    filled_slots = data.get('filledslots', {})
    reqslots = data.get('reqslots', [])
    domain = data.get('domain')
    intent = data.get('intent')
    is_final = data.get('final', False)

    # Recuperar dominio e intención si no vienen explícitamente
    if not domain:
        domain = list(tasks.keys())[0]
        intent = tasks[domain]
        data['domain'] = domain
        data['intent'] = intent

    # Si ya tenemos el servicio, hacemos slot filling final
    if service_id:
        return final_slot_filling(data)

    # Si hay múltiples servicios candidatos
    elif services:
        # Solo 'services' está definido, necesito seleccionar el servicio entre varios posibles
        if len(filled_slots) > len(reqslots):
            print("[DEBUG] Ya se han respondido preguntas adicionales. Vamos a final_slot_filling.")
            return final_slot_filling(data)
        else:
            print("No tengo preguntas intermedias aún, llamando a service_selection.")
            return service_selection(data)

    # Si aún no se han hecho preguntas
    else:
        if filled_slots and all(value != '' for value in filled_slots.values()):
            return service_selection(data)
        else:
            # Primer slot filling con top slots
            slots_list = call_disc_parameters(domain)
            top_slots = [slot['parameter'] for slot in slots_list]

            slots = call_slot_filling(user_input, top_slots)

            filled_params = {}
            questions = {}

            for slot_name, slot_value in slots.items():
                if slot_value is not None:
                    filled_params[slot_name] = slot_value
                else:
                    question = call_question_generation(slot_name, domain)
                    questions[slot_name] = question

            data['filledslots'] = filled_params

            if questions:
                return jsonify({
                    'questions': questions,
                    'filledslots': filled_params,
                    'intent': intent,
                    'userinput': user_input,
                    'dom': domain,
                    'reqslots': top_slots,
                    'tasks': tasks,
                    'final': False
                }), 202
            else:
                return service_selection(data)

def service_selection(data):
    emptyParams = {}
    filledParams = {}

    print("Received data from manage_task_oriented:", data)

    tasks = data.get('tasks')
    domain = data.get('domain')
    intent = data.get('intent')
    userInput = data.get('userinput')
    userAnswers = data.get('useranswers', [])
    reqSlots = data.get('reqslots')
    filledslots = data.get("filledslots", {})

    if check_for_goodbye(userInput):
        return jsonify({"chatbot_answer": "Thank you for chatting! Goodbye!", "end_conversation": True})

    dynamic_params = reqSlots

    # Si ya tengo suficientes slots, filtro los servicios
    if filledslots and all(filledslots.get(p, '') != '' for p in reqSlots):
        services = call_filter_services(data)
        print("[DEBUG] Respuesta de tagfilter_service:", services)

        if isinstance(services, dict) and "services" in services:
            selected_services = services["services"]
        else:
            selected_services = services

        print("[DEBUG] Selected_services es:", selected_services)

        if len(selected_services) > 1:
            aditional_questions, filledParams = call_get_aditional_questions(selected_services, userInput, intent, data, domain)
            services_as_strings = [str(s) for s in selected_services]

            return jsonify({
                'questions': aditional_questions,
                'filledslots': filledParams,
                'intent': intent,
                'userinput': userInput,
                'services': services_as_strings,
                'useranswers': userAnswers,
                'dom': domain,
                'reqslots': reqSlots,
                'tasks': tasks
            }), 202
        elif len(selected_services) == 1:
            service_id = str(selected_services[0])
            data["service_id"] = service_id
            return final_slot_filling(data)
        else:
            return jsonify({"error": "No services found"}), 404

    else:
        # Aún no se han rellenado todos los slots principales, se retorna sin filtrar
        return jsonify({
            'questions': {},
            'filledslots': filledslots,
            'intent': intent,
            'userinput': userInput,
            'services': [],
            'reqslots': reqSlots,
            'tasks': tasks
        }), 202

def call_get_aditional_questions(services, userInput, intent, data_from_client, domain):
    payload = {
        "services": [str(s) for s in services],
        "userinput": userInput,
        "intent": intent,
        "domain": domain,
        "filledslots": data_from_client.get("filledslots", {}),
        "useranswers": data_from_client.get("useranswers", []),
        "email": data_from_client.get("email", ""),
        "service_id": data_from_client.get("service_id", ""),
        "reqslots": data_from_client.get("reqslots", []),
        "tasks": data_from_client.get("tasks", {}),
        "final": False
    }

    print("[DEBUG] Datos enviados a /additional-questions:", json.dumps(payload, indent=2))

    response = requests.post(ADITIONAL_QUESTIONS_URL, json=payload)

    if response.status_code == 200:
        return response.json().get("additional_questions", {}), response.json().get("filledslots", {})
    else:
        print("[ERROR] Fallo en get_aditional_questions:", response.text)
        return {}, data_from_client.get("filledslots", {})

def call_disc_parameters(domain):
    response = requests.post(DISC_PARAMETER_URL, json={"domain": domain})
    return response.json()

def call_detect_positive_answers(filled_params):
    try:
        response = requests.post(DETECT_POSITIVE_URL, json={"filled_params": filled_params})
        if response.status_code == 200:
            return response.json().get("positive_tags", [])
        else:
            print(f"[ERROR] detect_positive_answers failed: {response.text}")
            return []
    except Exception as e:
        print(f"[ERROR] Exception in call_detect_positive_answers: {e}")
        return []

# Obtener la base de datos
db = MongoDB()

def call_filter_services_by_tag(intent_services, user_tags, domain):
    try:
        payload = {
            "intent_services": [str(s) for s in intent_services],
            "user_tags": user_tags,
            "domain": domain
        }
        response = requests.post(TAG_FILTER_URL, json=payload)
        response.raise_for_status()
        return response.json().get("filtered_services", {})
    except Exception as e:
        print(f"[ERROR] call_filter_services_by_tag falló: {e}")
        return {}

def clean_question_text(q):
    return re.sub(r'^[\'"]|[\'"]$', '', q.strip())

def final_slot_filling(data):
    print("[DEBUG][final_slot_filling] data recibido:", data)

    from bson import ObjectId
    import random

    user_input = data.get('userinput')
    user_answers = data.get('useranswers', [])
    domain = data.get('domain')
    intent = data.get('intent')
    tasks = data.get('tasks')
    reqslots = data.get('reqslots', [])
    services = data.get('services', [])
    service_id = data.get('service_id')
    filledParams = data.get('filledslots', {})
    emptyParams = {}

    if check_for_goodbye(user_input):
        return jsonify({"chatbot_answer": "Thank you for chatting! Goodbye!", "end_conversation": True})

    if not service_id:
        # Detectar respuestas positivas del usuario (e.g. terrace = yes)
        positive_tags = call_detect_positive_answers(filledParams)
        print("[DEBUG] TAGS POSITIVOS:", positive_tags)

        # Convertir los IDs a ObjectId para filtrado
        object_ids = [ObjectId(s) for s in services]
        filtered_services = call_filter_services_by_tag(object_ids, positive_tags, domain)
        print("[DEBUG] Servicios filtrados por tags:", filtered_services)

        # Elegir el mejor servicio (puede haber empate)
        max_score = max(filtered_services.values())
        best_services = [sid for sid, score in filtered_services.items() if score == max_score]
        service_id = random.choice(best_services)

    print("[DEBUG] Servicio seleccionado final:", service_id)

    # Extraer los slots esperados del servicio
    expected_slots = call_extract_slots(intent, str(service_id), domain)

    # Hacer slot filling final incluyendo el historial
    slotFillingResponse = call_slot_filling(user_input, expected_slots, user_answers)
    print("[DEBUG] Los slots rellenos con el cambio son:", slotFillingResponse)

    # Clasificar slots en llenos o vacíos
    for key, value in slotFillingResponse.items():
        if value == "Null" or value is None:
            emptyParams[key] = value
        else:
            filledParams[key] = value

    # Eliminar reqslots de los que aún están vacíos
    for param in reqslots:
        emptyParams.pop(param, None)

    print("[DEBUG] EMPTY PARAMS:", emptyParams)
    print("[DEBUG] FILLED PARAMS:", filledParams)

    # Obtener las preguntas a partir del servicio
    question_slots = call_question_retrieval(str(service_id), intent, domain).get("questions", {})
    questions = {}

    for empty in emptyParams:
        if empty in question_slots:
            improved_question = call_question_improvement(question_slots[empty], domain)
            if improved_question:  # Solo incluir si hay resultado válido
                questions[empty] = clean_question_text(improved_question)
            else:
                print(f"[ERROR] No se pudo mejorar la pregunta para el slot: {empty}")

    print("PREGUNTAS FINALES A ENVIAR:", questions)
    print("TIPOS DE DATOS:", {k: type(v) for k, v in questions.items()})

    return jsonify({
        'questions': questions,
        'filledslots': filledParams,
        'service_id': str(service_id),
        'intent': intent,
        'dom': domain,
        'tasks': tasks,
        'final': True,
        'reqslots': reqslots
    }), 202

def send_data_to_server(data):
    tasks = data.get('tasks', {})
    if not tasks:
        print("Tasks está vacío desde el principio.")
        dialogue_history['useranswers'] = []  # Limpiar historial
        return jsonify({'end_of_conversation': True}), 202

    # Seleccionar la primera tarea
    current_domain = data['domain']
    current_intent = tasks[current_domain]
    print(f"Procesando dominio actual: {current_domain}, intent: {current_intent}")

    # Simular la llamada al servidor (puedes usar la lógica real aquí)
    # service_response = simulate_service_call(data)

    # Eliminar la tarea completada
    del tasks[current_domain]
    print(f"Tarea eliminada: {current_domain}. Tareas restantes: {tasks}")
    data['tasks'] = tasks

    # Si no hay más tareas, finalizar conversación
    if not tasks:
        print("No quedan más tareas. Finalizando conversación.")
        dialogue_history['useranswers'] = []  # Limpiar historial
        return jsonify({'end_of_conversation': True}), 202

    # Preparar datos para la siguiente tarea
    next_domain = next(iter(tasks))
    next_intent = tasks[next_domain]
    data.update({
        'domain': next_domain,
        'intent': next_intent,
        'filledslots': {},  # Reiniciar slots llenados
        'service_id': '',  # Reiniciar ID del servicio
        'useranswers': [],  # Reiniciar respuestas del usuario
        'questions': {},  # Reiniciar preguntas
        'final': False,  # Asegurarse de que no termine aún
        'reqslots': [],  # Reiniciar slots requeridos
        'userinput': data['userinput']  # Mantener el input del usuario
    })
    print("Datos preparados para la siguiente tarea:", data)

    # Llamar nuevamente a chatbot con los datos actualizados
    return chatbot(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)