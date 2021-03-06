from django.contrib import admin

from.models import *

# Register your models here.
@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post']

admin.site.register(Grade)

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'title', 'hide', 'real_created_date', 'created_date']
    list_display_links = ['id', 'title']
    list_filter = ['author']
    list_per_page = 30

@admin.register(ThreadAnalytics)
class ThreadAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'thread', 'count']
    list_display_links = ['id', 'thread']
    list_filter = ['date']
    list_per_page = 30

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'thread', 'created_date']
    list_filter = ['author']
    list_per_page = 30

@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'agree_email', 'agree_history', 'telegram_id', 'telegram_token', 'password_qna']
    actions = ['send_report']

    def send_report(self, request, queryset):
        pass
        # updated_count = queryset.update(hide=True)
        # self.message_user(request, str(updated_count) + '명에게 보고서 전송')
    
    send_report.short_description = '보고서 전송'

@admin.register(TempPosts)
class TempPostsAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'title', 'token', 'created_date',]
    list_display_links = ['id', 'title']
    list_filter = ['author']
    list_per_page = 30
    
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'title', 'hide', 'created_date', 'updated_date']
    list_display_links = ['id', 'title']
    list_filter = ['author']
    actions = ['make_open', 'make_hide']
    list_per_page = 30

@admin.register(PostLikes)
class PostLikesAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_date']
    list_filter = ['user']

@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'posts', 'count']
    list_display_links = ['id', 'posts']
    list_filter = ['date']
    list_per_page = 30

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'text', 'created_date']
    list_filter = ['author']
    list_per_page = 30

@admin.register(Notify)
class NotifyAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'infomation', 'created_date']

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'name', 'created_date']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'grade']
    list_editable = ['grade']