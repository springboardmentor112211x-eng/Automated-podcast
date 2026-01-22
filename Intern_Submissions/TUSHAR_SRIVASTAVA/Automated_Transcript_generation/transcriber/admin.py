# transcriber/admin.py
from django.contrib import admin
from .models import Podcast

@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('title', 'user', 'status', 'detected_language', 'created_at')
    
    # Filters to quickly find processing or failed tasks
    list_filter = ('status', 'detected_language', 'created_at')
    
    # Search functionality for titles and usernames
    search_fields = ('title', 'user__username', 'transcript_raw')
    
    # Grouping fields in the detail view
    fieldsets = (
        ('Podcast Info', {
            'fields': ('user', 'title', 'audio_file', 'status')
        }),
        ('AI Generation (Raw)', {
            'fields': ('detected_language', 'transcript_raw'),
            'classes': ('collapse',)  # Keeps it tidy
        }),
        ('Human Supervision (Final)', {
            'fields': ('transcript_final',)
        }),
    )
    
    # Ensures transcript_raw is readable but not editable in admin if preferred
    # readonly_fields = ('transcript_raw', 'detected_language')