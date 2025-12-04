import uuid

def get_chat_user(request):
    if request.user.is_authenticated:
        return request.user

    # fallback for anonymous users
    if "chat_user_key" not in request.session:
        request.session["chat_user_key"] = f"anon_{uuid.uuid4().hex}"

    return request.session["chat_user_key"]
