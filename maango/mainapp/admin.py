from django.contrib import admin

# Register your models here.
from .models import *

# Register the model
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Problem)
admin.site.register(UserProfile)