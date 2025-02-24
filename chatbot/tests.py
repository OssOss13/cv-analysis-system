from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
import json

class ChatbotViewsTest(TestCase):
    def test_chatbot_page_loads(self):
        """Test if the chatbot interface page loads"""
        response = self.client.get(reverse("chatbot"))  # Ensure this matches your URL name
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chatbot/chat.html")
