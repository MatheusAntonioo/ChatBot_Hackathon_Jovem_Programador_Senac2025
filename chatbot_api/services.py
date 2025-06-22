# chatbot_app/services.py

from openai import OpenAI
import os

client = OpenAI()

def get_openai_response(prompt_text, system_prompt_override=None): # <--- GARANTA que este parâmetro está aqui
    """
    Envia um prompt para a API da OpenAI e retorna a resposta do modelo.
    Permite sobrescrever o system_prompt.
    """
    try:
        initial_system_prompt = system_prompt_override if system_prompt_override else "Você é uma assistente prestativa, jovem, muito educada e amigável."

        messages = [
            {"role": "system", "content": initial_system_prompt},
            {"role": "user", "content": prompt_text}
        ]

        chat_completion = client.chat.completions.create( # E verifique se está 'completions.create'
            model="gpt-4o",  
            messages=messages,
            max_tokens=500,  
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Erro ao chamar a API da OpenAI: {e}")
        return "Desculpe, não consegui processar sua solicitação no momento."