import json

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import DatabaseError
from django.utils import timezone
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
        recipient_list = [note.user.email]  # Replace with the actual recipient's email

        # Send the email
        send_mail(subject, message, from_email, recipient_list)

        logger.success(f"Reminder email sent for Note: {note_data['title']} at {note_data['reminder']}")

    except ObjectDoesNotExist:
        logger.warning(f"Note with ID {note_id} does not exist.")
    except DatabaseError as e:
        logger.error(f"Database error while sending reminder for note {note_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while sending reminder for note {note_id}: {e}")

@shared_task
def check_reminders():
    """
    Periodic task to check for notes with reminders that need to be sent.
    """
    now = timezone.now()
    # Fetch notes with reminders that need to be sent
    notes_with_reminders = Note.objects.filter(reminder__lte=now, is_reminded=False)
    
    for note in notes_with_reminders:
        send_reminder.delay(note.id)  # Send the reminder
        note.is_reminded = True  # Mark the note as reminded
        note.save()



def schedule_reminder(note):
    """
    Schedule the reminder email to be sent at the note's reminder time.
    """
    reminder_time = note.reminder

    if reminder_time and reminder_time > timezone.now():
        # Schedule the task to be executed at the reminder time
        send_reminder((note.id,), eta=reminder_time)
        logger.info(f"Reminder for Note: {note.title} scheduled at {reminder_time}")
    else:
        logger.warning(f"Invalid or past reminder time for Note: {note.title}")
