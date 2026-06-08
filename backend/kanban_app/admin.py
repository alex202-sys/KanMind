from django.contrib import admin
from .models import Comment, Task, Board

# Register your models here.
admin.site.register(Comment)
admin.site.register(Task)
admin.site.register(Board)
