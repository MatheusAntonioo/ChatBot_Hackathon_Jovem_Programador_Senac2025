from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import asyncio 
from django.utils import timezone
from asgiref.sync import sync_to_async

from .utils import scrape_jovemprogramador_playwright
from .services import get_openai_response
from .models import Message
from asgiref.sync import sync_to_async

from .utils import scrape_jovemprogramador_playwright
from .services import get_openai_response
from .models import Message

@csrf_exempt
async def chatbot_view(request):
    session_id = request.session.session_key 
    if not session_id:
        await sync_to_async(request.session.save)()
        session_id = request.session.session_key

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message_text = data.get('message', '').lower()

            await sync_to_async(Message.objects.create)(
                session_id=session_id,
                sender='user',
                text=user_message_text
            )
            print(f"Mensagem do usuário salva: {user_message_text}")

            bot_response_text = ""

            # --- Lógica para determinar o system_prompt com base na pergunta ---

            # 1. Prioridade: Perguntas sobre a criação/hackaton (resposta fixa)
            hackaton_keywords = ['qual linguagem?', 'qual a linguagem você foi desenvolvida?', 'em que linguagem você foi desenvolvida?', 'qual linguagem usada?', ]
            if any(keyword in user_message_text for keyword in hackaton_keywords):
                bot_response_text = (
                    "Estou sendo desenvolvida na linguagem Python, utilizando o framework Django entre outras ferramentas!"
                )

            # 1. Prioridade: Perguntas sobre a criação/hackaton (resposta fixa)
            hackaton_keywords2 = ['qual sua idade?', 'quantos anos tem?', 'quantos anos você tem?' ]
            if any(keyword in user_message_text for keyword in hackaton_keywords2):
                bot_response_text = (
                    "Ainda não saí do forno! Mas quando sair, lá por novembro de 2025, prometo que serei deliciosa."
                    "😜"
                )

            # 2. Segunda prioridade: Perguntas sobre a identidade geral da ADA (nome, quem é, propósito)
            # Nestes casos, a ADA DEVE usar conhecimento geral, não o site.
            
            elif any(keyword in user_message_text for keyword in ['qual seu nome?', 'porque ADA?', 'porque este nome?']):
                system_prompt_ada_identity = (
                    "respoonda sempre educadamente e de forma clara. "
                    "responda que seu nomé é em homenagem a ADA LOVELACE tirando um texto curto sobre ela na internet."
                )
                # Não precisamos raspar o site para estas perguntas, então a chamada à raspagem é pulada.
                bot_response_text = get_openai_response(user_message_text, system_prompt_override=system_prompt_ada_identity)

            # 3. Última prioridade: Todas as outras perguntas (raspar o site)
            else:
                scraped_content = ""
                alert_message = ""
                print(f"Tentando raspar jovemprogramador.com.br com Playwright.")
                # NÂO passe query_keywords aqui, pois já tiramos essa lógica do utils.py
                scraped_result = await scrape_jovemprogramador_playwright() 

                if scraped_result == "CONTEUDO_NAO_ENCONTRADO_SITE":
                    alert_message = "Apesar de ter acessado o site Jovem Programador, não encontrei informações relevantes ou específicas sobre sua pergunta no conteúdo que pude raspar. Tente refinar sua pergunta ou verificar o site diretamente."
                    scraped_content = "" # Garante que scraped_content está vazio se nada foi encontrado
                else: # Se houver conteúdo, scraped_result será o texto
                    scraped_content = scraped_result
                    print(f"Conteúdo raspado com sucesso do Jovem Programador ({len(scraped_content)} chars).")

                # System prompt para perguntas baseadas no site
                system_prompt_site = (
                    "Você é ADA, uma assistente virtual criada para responder dúvidas com base em informações confiáveis do site Jovem Programador. "
                    "Não use conhecimento geral da internet para responder a perguntas que se referem ao site. Se não se referir ao site avise e responda com base na internet de forma coerente. "
                    "Seja sempre prestativa, clara e educada nas respostas."
                )

                if scraped_content and scraped_content != "CONTEUDO_NAO_ENCONTRADO_SITE": # Verificação dupla
                    system_prompt_site += f" As seguintes informações foram raspadas do site Jovem Programador: {scraped_content}. Responda à pergunta do usuário usando APENAS essas informações. Se a resposta para a pergunta do usuário não estiver clara e diretamente no texto fornecido, diga claramente que a informação não foi encontrada no site Jovem Programador."
                else:
                    system_prompt_site += f" {alert_message} Portanto, não posso responder a essa pergunta com informações do site Jovem Programador. Não tente inventar uma resposta com base em conhecimento generalizado."

                bot_response_text = get_openai_response(user_message_text, system_prompt_override=system_prompt_site)

            # Salvar mensagem do bot
            await sync_to_async(Message.objects.create)(
                session_id=session_id,
                sender='bot',
                text=bot_response_text
            )
            print(f"Mensagem do bot salva: {bot_response_text[:50]}...")

            return JsonResponse({'response': bot_response_text})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Requisição inválida (JSON).'}, status=400)
        except Exception as e:
            print(f"Erro geral na chatbot_view: {e}")
            error_response_text = f'Ocorreu um erro interno: {e}'
            await sync_to_async(Message.objects.create)(
                session_id=session_id,
                sender='bot',
                text=error_response_text
            )
            return JsonResponse({'error': error_response_text}, status=500)

    return render(request, 'chatbot_app/index.html')