from django.contrib import admin
from .models import AreaCode, AreaData

@admin.register(AreaCode)
class AreaCodeAdmin(admin.ModelAdmin):
    pass

@admin.register(AreaData)
class AreaDataAdmin(admin.ModelAdmin):
    pass