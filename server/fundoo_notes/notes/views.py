from django.shortcuts import render
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
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
        return Note.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the note is saved with the authenticated user
        serializer.save(user=self.request.user)

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
