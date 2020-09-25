from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Post, Comment, DetailPostImage, DetailPostLocation, PostDate, Tag

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass

@admin.register(PostDate)
class PostDateAdmin(admin.ModelAdmin):
    pass

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass

@admin.register(DetailPostImage)
class DetailPostImageAdmin(admin.ModelAdmin):
    pass

@admin.register(DetailPostLocation)
class DetailPostLocationAdmin(admin.ModelAdmin):
    pass

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass
