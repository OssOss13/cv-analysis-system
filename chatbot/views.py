import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rag.agent import invoke_cv_agent
from .models import Conversation, Message
import logging

logger = logging.getLogger(__name__)

def chatbot_view(request):
    return render(request, "chatbot/chat.html")

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            user_id = data.get("user_id", "anonymous")
            
            if not user_message:
                return JsonResponse({"error": "No message provided"}, status=400)

            # Retrieve or create conversation 
            conversation, _ = Conversation.objects.get_or_create(user_id=user_id)

            # Save message to db
            Message.objects.create(conversation=conversation, sender="user", text=user_message)

            # Retrieve last 10 messages for history
            # We want them in chronological order for the agent
            previous_messages = conversation.messages.order_by('-timestamp')[:10]
            # Reverse to get chronological order
            previous_messages = reversed(previous_messages)
            
            chat_history = []
            for msg in previous_messages:
                # Skip the current message we just added (it's the last one)
                # Actually, invoke_cv_agent expects history WITHOUT the current query usually,
                # or we can handle it. The agent.py says:
                # "messages": formatted_history + [HumanMessage(content=query)]
                # So we should NOT include the current message in history.
                
                # But we just saved it. So we need to exclude it.
                if msg.text == user_message and msg.sender == "user":
                    # This is a bit risky if user sends same message twice.
                    # Better to just take all messages except the last one?
                    # But we are iterating a query set.
                    pass
                
                # Let's just rebuild history from DB excluding the very last one we just inserted.
                # Or simpler: just pass the history. invoke_cv_agent takes query and history.
                pass

            # Let's re-fetch history properly
            # Get all messages for this conversation
            all_messages = conversation.messages.order_by('timestamp')
            # Exclude the last one (current query)
            history_messages = all_messages[:len(all_messages)-1]
            # Take last 10
            history_messages = history_messages[-10:]
            
            chat_history = []
            for msg in history_messages:
                chat_history.append({
                    "sender": msg.sender,
                    "text": msg.text
                })

            # Generate response using Agent
            result = invoke_cv_agent(user_message, chat_history)
            bot_response = result["answer"]
            
            # Save bot response to db
            Message.objects.create(conversation=conversation, sender='bot', text=bot_response)

            return JsonResponse({"response": bot_response})

        except Exception as e:
            logger.error(f"Error in chatbot_response: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)
        
    return JsonResponse({"error": "Invalid request"}, status=400)
