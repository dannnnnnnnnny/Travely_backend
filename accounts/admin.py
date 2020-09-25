from django.contrib import admin
from .models import User, Concept, Area, MapData


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    pass

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    pass

@admin.register(MapData)
class MapDataAdmin(admin.ModelAdmin):
    pass
