import traceback
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation, Message
from .utils import filter_data_from_db, classify_query_with_gpt, get_all_records_by_candidate, summarize_and_remove_dups, add_context_to_final_message


def chatbot_view(request):
    return render(request, "chatbot/chat.html")


@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            user_id = data.get("user_id", "anonymous")
            
            print(f"User Message: {user_message}")  # Debugging output
            print(f"User ID: {user_id}")

            if not user_message:
                return JsonResponse({"error": "No message provided"}, status=400)

            # Retrieve or create conversation 
            conversation, _ = Conversation.objects.get_or_create(user_id=user_id)

            # Save message to db
            Message.objects.create(conversation=conversation, sender="user", text=user_message)

            # retrieve past 5 messages
            past_messages = list(conversation.messages.order_by("-timestamp").values("sender", "text")[:5]) # last 5 msgs only
            formatted_history = [
                {"role": "user" if msg["sender"] == "user" else "assistant", "content": msg["text"]}
                for msg in past_messages
            ]
            print('----------------------')
            print(formatted_history)
            # get relevant info from db

            user_message_lower = user_message.lower()
            classified_query = classify_query_with_gpt(user_message_lower)

            relevant_data = ''

            if classified_query.startswith("general:"):
                table_name = classified_query.split(":")[1]
                relevant_data = get_all_records_by_candidate(table_name)

            elif classified_query.startswith("filter:"):
                _, keyword, table_name = classified_query.split(":")
                relevant_data = filter_data_from_db(table_name, keyword)

            # Summarize relevant info 
            summarized_data = summarize_and_remove_dups(relevant_data)

            
            bot_response = add_context_to_final_message(summarized_data, formatted_history, user_message)
            
            # save bot response to db
            Message.objects.create(conversation=conversation, sender='bot', text=bot_response)

            # bot_response = 'done'

            return JsonResponse({"response": bot_response})

        except Exception as e:
            print("Error:", str(e))  # Debugging output
            traceback.print_exc()  # Print full error traceback
            return JsonResponse({"error": str(e)}, status=500)
        
    return JsonResponse({"error": "Invalid request"}, status=400)

