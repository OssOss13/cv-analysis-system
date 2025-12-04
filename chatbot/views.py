import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rag.agent import invoke_cv_agent
from .models import Conversation, Message
import logging
from .utils import get_chat_user
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def chatbot_view(request):
    return render(request, "chatbot/chat.html")

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            if not user_message:
                return JsonResponse({"error": "No message provided"}, status=400)

            identifier = get_chat_user(request)

            if isinstance(identifier, User):
                conversation, _ = Conversation.objects.get_or_create(user=identifier)
            else:
                conversation, _ = Conversation.objects.get_or_create(anon_user_id=identifier)

            # save incoming message
            Message.objects.create(conversation=conversation, sender="user", text=user_message)

            # fetch last messages except current
            all_messages = conversation.messages.order_by("timestamp")
            history_messages = all_messages[:len(all_messages)-1][-3:]

            chat_history = [{"sender": msg.sender, "text": msg.text} for msg in history_messages]

            # agent response
            result = invoke_cv_agent(user_message, chat_history)
            bot_response = result["answer"]

            # save bot reply
            Message.objects.create(conversation=conversation, sender="bot", text=bot_response)

            return JsonResponse({"response": bot_response})

        except Exception as e:
            logger.error(f"Error in chatbot_response: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)