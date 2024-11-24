from django.contrib import admin

# Register your models here.

from .models import User, Result, Post, Skill

admin.site.register(User)
admin.site.register(Result)
admin.site.register(Post)
admin.site.register(Skill)
