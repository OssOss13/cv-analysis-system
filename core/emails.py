from django.core.mail import send_mail
from core.settings import DEFAULT_FROM_EMAIL

def send_application_confirmation(candidate_name, position_title, to_email):
    """
    Send an application confirmation email to one or more recipients.
    :param candidate_name: Name of the candidate
    :param position_title: Title of the position applied for
    :param to_email: List of recipient email addresses (JSONField from CVSummary)
    """
    subject = f"Your application for {position_title} has been received"
    message = (
        f"Hello,\n\n"
        f"Thank you {candidate_name} for applying for the position: {position_title}.\n"
        f"Our team has received your CV and it is now being processed.\n\n"
        f"Best regards,\nYour Hiring Team"
    )

    to_email_list = to_email
    if isinstance(to_email_list, str):
        to_email_list = [to_email_list]

    send_mail(
        subject,
        message,
        DEFAULT_FROM_EMAIL,
        to_email_list,
        fail_silently=False,
    )