from django.shortcuts import render
from loguru import logger
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    queryset = Note.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        # Only return notes belonging to the authenticated user
        logger.debug(f"Authenticated user: {self.request.user}")
        return Note.objects.filter(user=self.request.user)


    def create(self, request, *args, **kwargs):
        """
        Create a new note and associate it with the authenticated user.
        """

        data = request.data
        data['user'] = request.user.id  # Automatically associate the note with the logged-in user

        logger.info(f"Creating note for user: {data}")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)  # Validate data
        
        logger.info(f"Creating note for user: {data}")
        
        # Save the note with the authenticated user
        serializer.save()

        return Response({
            "message": "Note created successfully",
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


    # Retrieve a single note
    def retrieve(self, request, *args, **kwargs):
        note = self.get_object()
        if note.user != self.request.user:
            raise PermissionDenied("You do not have permission to view this note.")
        serializer = self.get_serializer(note)

        return Response({
            "message": "Note retrieved successfully",
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


    # List all notes for the authenticated user
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Notes retrieved successfully",
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


    # Update an existing note
    def update(self, request, *args, **kwargs):
        note = self.get_object()

        if note.user != self.request.user:
            raise PermissionDenied("You do not have permission to edit this note.")
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(note, data=request.data, partial=partial)

        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "message": "Note updated successfully",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "message": "Error updating note",
            "status": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # Delete a note
    def destroy(self, request, *args, **kwargs):
        note = self.get_object()
        if note.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this note.")
        self.perform_destroy(note)

        return Response({
            "message": "Note deleted successfully",
            "status": "success"
        }, status=status.HTTP_204_NO_CONTENT)
    
    # """
    # Viewset to handle CRUD operations for notes and special archive/trash actions.
    # """

    @action(detail=True, methods=['patch'])
    def archive(self, request, pk=None):
        """
        Update the archive status of a note.
        """
        try:
            note = self.get_object()
            note.is_archive = not note.is_archive
            note.save()

            return Response({
                "message": "Note archive status updated",
                "status": "success",
                "data": NoteSerializer(note).data
            }, status=status.HTTP_200_OK)
        
        except Note.DoesNotExist:
            logger.error(f"Note with id {pk} not found")
            return Response({
                "message": "Note not found",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            return Response({
                "message": str(e),
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error updating archive status: {str(e)}")
            return Response({
                "message": "An error occurred while updating the archive status",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def trash(self, request, pk=None):
        """
        Update the trash status of a note.
        """
        try:
            note = self.get_object()
            note.is_trash = not note.is_trash
            note.save()
            return Response({
                "message": "Note trash status updated",
                "status": "success",
                "data": NoteSerializer(note).data
            }, status=status.HTTP_200_OK)
        
        except Note.DoesNotExist:
            logger.error(f"Note with id {pk} not found")
            return Response({
                "message": "Note not found",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            return Response({
                "message": str(e),
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error updating trash status: {str(e)}")
            return Response({
                "message": "An error occurred while updating the trash status",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def archived_notes(self, request):
        """
        Get all archived notes for the authenticated user.
        """
        try:
            notes = Note.objects.filter(user=self.request.user, is_archive=True,is_trash =False)
            return Response({
                "message": "Archived notes fetched successfully",
                "status": "success",
                "data": NoteSerializer(notes, many=True).data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching archived notes: {str(e)}")
            return Response({
                "message": "An error occurred while fetching archived notes",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    @action(detail=False, methods=['get'])
    def trashed_notes(self, request):
        """
        Get all trashed notes for the authenticated user.
        """
        try:
            notes = Note.objects.filter(user=self.request.user, is_trash=True)
            return Response({
                "message": "Trashed notes fetched successfully",
                "status": "success",
                "data": NoteSerializer(notes, many=True).data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching trashed notes: {str(e)}")
            return Response({
                "message": "An error occurred while fetching trashed notes",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

