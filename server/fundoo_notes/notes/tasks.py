import json

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import DatabaseError
from loguru import logger
from utils.utils import RedisUtils

from .models import Note


@shared_task
def send_reminder(note_id):
    """
    Task to send a reminder for the given note.
    """
    redis = RedisUtils()
    try:
        # Try to fetch note from Redis cache first
        cache_key = f"note_{note_id}"
        note_data = redis.get(cache_key)

        if note_data:
            logger.info(f"Fetched note {note_id} from cache.")
            note_data = json.loads(note_data)
        else:
            # If not in cache, fetch from the database
            note = Note.objects.get(id=note_id)
            note_data = {
                'id': note.id,
                'title': note.title,
                'reminder': note.reminder.isoformat() if note.reminder else None,  # Convert to ISO format
                'user_id': note.user_id
            }

            # Save to Redis for future use
            redis.save(cache_key, json.dumps(note_data))
            logger.info(f"Saved note {note_id} to cache.")

        
        # Logic to send reminder (email, notification, etc.)
        subject = f"Reminder for your note: {note_data['title']}"
        message = f"Reminder: {note_data['title']}\nScheduled at: {note_data['reminder']}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ['recipient@example.com']  # Replace with the actual recipient's email

        # Send the email
        send_mail(subject, message, from_email, recipient_list)

        logger.success(f"Reminder email sent for Note: {note_data['title']} at {note_data['reminder']}")

        # # Logic to send reminder (email, notification, etc.)
        # logger.success(f"Reminder sent for Note: {note_data['title']} at {note_data['reminder']}")

    except ObjectDoesNotExist:
        logger.warning(f"Note with ID {note_id} does not exist.")
    except DatabaseError as e:
        logger.error(f"Database error while sending reminder for note {note_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while sending reminder for note {note_id}: {e}")

