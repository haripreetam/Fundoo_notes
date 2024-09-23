from celery import shared_task
from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from loguru import logger


@shared_task
def send_verification_email(user_email, verification_link):

    logger.info(f"Sending verification email to {user_email}")

    
    subject = "Verify your email"
    message = f"Click the link to verify your email: {verification_link}"
    email_from = settings.EMAIL_HOST_USER
    # recipient_list = [user_email]
    # fail_silently=False

    try:
        send_mail(
            subject,
            message,
            email_from,
            [user_email],
            fail_silently=False,
        )
    except BadHeaderError:
        # Handle bad header errors specifically
        print(f"Bad header error while sending email to {user_email}")


