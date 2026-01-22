from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import Room, Player, GameState, Question, Answer, StandaloneRequest
from .services import TurnManagementService


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['code', 'created_at', 'is_active', 'player_count', 'current_round', 'current_player', 'action_buttons']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code']
    readonly_fields = ['code', 'created_at']
    actions = []  # Explicitly set to empty list to avoid conflicts
    
    def player_count(self, obj):
        return obj.players.count()
    player_count.short_description = 'Players'
    
    def current_round(self, obj):
        game_state = obj.get_current_game_state()
        if game_state:
            return game_state.round_number
        return '-'
    current_round.short_description = 'Round'
    
    def current_player(self, obj):
        game_state = obj.get_current_game_state()
        if game_state and game_state.current_turn_player:
            return game_state.current_turn_player.name
        return '-'
    current_player.short_description = 'Current Player'
    
    def action_buttons(self, obj):
        if obj.is_active and obj.players.count() == 2:
            return format_html(
                '<a class="button" href="#" onclick="injectQuestion(\'{}\'); return false;">Inject Question</a>',
                obj.code
            )
        return '-'
    action_buttons.short_description = 'Actions'
    
    class Media:
        js = ('admin/js/inject_question.js',)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'room', 'join_order', 'created_at']
    list_filter = ['room', 'created_at']
    search_fields = ['name', 'room__code']


@admin.register(GameState)
class GameStateAdmin(admin.ModelAdmin):
    list_display = ['room', 'current_turn_player', 'round_number', 'current_choice', 'created_at']
    list_filter = ['round_number', 'created_at']
    search_fields = ['room__code']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['room', 'question_type', 'source', 'text_preview', 'is_answered', 'created_at']
    list_filter = ['question_type', 'source', 'is_answered', 'created_at']
    search_fields = ['room__code', 'text']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['player', 'question', 'answer_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['player__name', 'answer_text']
    
    def answer_preview(self, obj):
        return obj.answer_text[:50] + '...' if len(obj.answer_text) > 50 else obj.answer_text
    answer_preview.short_description = 'Answer'


@admin.register(StandaloneRequest)
class StandaloneRequestAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'question_type', 'question_source', 'question_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'question_type', 'question_source', 'created_at']
    search_fields = ['user_name', 'session_id', 'current_question']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    def question_preview(self, obj):
        if obj.current_question:
            return obj.current_question[:50] + '...' if len(obj.current_question) > 50 else obj.current_question
        return '-'
    question_preview.short_description = 'Current Question'
