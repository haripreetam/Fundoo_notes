import json
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from loguru import logger
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from utils.utils import RedisUtils

from .models import Note
from .serializers import NoteSerializer
from .tasks import send_reminder


class NoteViewSet(viewsets.ViewSet):
    """
    A ViewSet for viewing, editing, archiving, and trashing user notes.

    desc: Handles CRUD operations and custom actions for user notes.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = RedisUtils()

    def list(self, request):
        """
        desc: Fetches all notes for the authenticated user.
        params: request (Request): The HTTP request object.
        return: Response: Serialized list of notes or error message.
        """
        try:
            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)

            if notes_data:
                logger.info("Returning notes from cache.")
                notes_data = json.loads(notes_data) # type: ignore
            else:
                queryset = Note.objects.filter(user=request.user)
                serializer = NoteSerializer(queryset, many=True)
                notes_data = serializer.data
                logger.info(f"info {notes_data}")

                notes_data_str = json.dumps(notes_data)
                self.redis.save(cache_key, notes_data_str)

            logger.success(f"Successfully retrieved notes for user {request.user.id}.")
            return Response({
                "message": "Notes retrieved successfully",
                "status": "success",
                "data": notes_data
            })

        except DatabaseError as e:
            logger.error(f"Database error while fetching notes: {e}")
            return Response(
                {
                    'message': 'Failed to fetch notes',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while fetching notes: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """
        desc: Creates a new note for the authenticated user.
        params: request (Request): The HTTP request object with note data.
        return: Response: Serialized note data or error message.
        """
        try:
            serializer = NoteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            note = serializer.save(user=request.user)

            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) # type: ignore
            else:
                notes_data = []

            notes_data.append(serializer.data)
            self.redis.save(cache_key, json.dumps(notes_data))

            # setting the reminder
            reminder_time = request.data.get('reminder')
            if reminder_time:
                send_reminder.delay(note.id)

            logger.success(f"Note created successfully for user {request.user.id}")
            return Response({
                "message": "Note created successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except DatabaseError as e:
            logger.error(f"Database error while creating note: {e}")
            return Response(
                {
                    'message': 'Failed to create note',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error while creating note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, pk=None):
        """
        desc: Retrieves a specific note for the authenticated user.
        params:
            request (Request): The HTTP request object.
            pk (int): Primary key of the note.
        return: Response: Serialized note data or error message.
        """
        try:
            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)

            if notes_data:
                notes_data = json.loads(notes_data) # type: ignore
                note_data = next(
                    (note for note in notes_data if note['id'] == int(pk)), None)  # type: ignore
                if note_data:
                    logger.info(f"Returning note {pk} from cache.")
                    return Response({
                        "message": "Note retrieved successfully",
                        "status": "success",
                        "data": note_data
                    })
                else:
                    raise ObjectDoesNotExist

            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note)
            note_data = serializer.data

            logger.success(f"Note {pk} retrieved successfully for user {request.user.id}")
            self.redis.save(cache_key, json.dumps(note_data))
            return Response({
                "message": "Note retrieved successfully",
                "status": "success",
                "data": note_data
            })

        except ObjectDoesNotExist:
            logger.warning(f"The requested note with id {pk} does not exist.")
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while retrieving note: {e}")
            return Response(
                {
                    'message': 'Failed to retrieve note',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while retrieving note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None):
        """
        desc: Updates a specific note for the authenticated user.
        params:
            request (Request): The HTTP request object with note data.
            pk (int): Primary key of the note.
        return: Response: Serialized note data or error message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note, data=request.data)
            serializer.is_valid(raise_exception=True)
            note = serializer.save()

            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) # type: ignore
                for idx, existing_note in enumerate(notes_data):
                    if existing_note['id'] == int(pk):  # type: ignore
                        notes_data[idx] = serializer.data
                        break

                self.redis.save(cache_key, json.dumps(notes_data))

            # Send reminder if it exists
            reminder_time = request.data.get('reminder')
            if reminder_time:
                send_reminder.delay(note.id)  # Schedule the reminder task

            return Response({
                "message": "Note updated successfully",
                "status": "success",
                "data": serializer.data
            })

        except ObjectDoesNotExist:
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while updating note: {e}")
            return Response(
                {
                    'message': 'Failed to update note',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error while updating note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        """
        desc: Deletes a specific note for the authenticated user.
        params:
            request (Request): The HTTP request object.
            pk (int): Primary key of the note.
        return: Response: Success message or error message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.delete()

            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) # type: ignore
                notes_data = [
                    note for note in notes_data if note['id'] != int(pk)]  # type: ignore

                self.redis.save(cache_key, json.dumps(notes_data))

            return Response({
                "message": "Note deleted successfully",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)

        except ObjectDoesNotExist:
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while deleting note: {e}")
            return Response(
                {
                    'message': 'Failed to delete note',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error while deleting note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def archive(self, request):
        """
        desc: Archives the specified note for the authenticated user.
        params: request (Request): The HTTP request object with note ID.
        return: Response: Success message or error message.
        """
        try:
            note_id = request.data.get('note_id')
            note = Note.objects.get(pk=note_id, user=request.user)
            note.is_archived = True  # type: ignore
            note.save()

            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) # type: ignore
                for idx, existing_note in enumerate(notes_data):
                    if existing_note['id'] == int(note_id):
                        existing_note['is_archived'] = True
                        break

                self.redis.save(cache_key, json.dumps(notes_data))

            return Response({
                "message": "Note archived successfully",
                "status": "success"
            })

        except ObjectDoesNotExist:
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while archiving note: {e}")
            return Response(
                {
                    'message': 'Failed to archive note',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error while archiving note: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def trash(self, request):
        """
        desc: Moves the specified note to trash for the authenticated user.
        params: request (Request): The HTTP request object with note ID.
        return: Response: Success message or error message.
        """
        try:
            note_id = request.data.get('note_id')
            note = Note.objects.get(pk=note_id, user=request.user)
            note.is_trashed = True  # type: ignore
            note.save()

            cache_key = request.user.id
            notes_data = self.redis.get(cache_key)
            if notes_data:
                notes_data = json.loads(notes_data) # type: ignore
                for idx, existing_note in enumerate(notes_data):
                    if existing_note['id'] == int(note_id):
                        existing_note['is_trashed'] = True
                        break

                self.redis.save(cache_key, json.dumps(notes_data))

            return Response({
                "message": "Note moved to trash successfully",
                "status": "success"
            })

        except ObjectDoesNotExist:
            return Response(
                {
                    'message': 'Note not found',
                    'status': 'error',
                    'errors': 'The requested note does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError as e:
            logger.error(f"Database error while moving note to trash: {e}")
            return Response(
                {
                    'message': 'Failed to move note to trash',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error while moving note to trash: {e}")
            return Response(
                {
                    'message': 'An unexpected error occurred',
                    'status': 'error',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )