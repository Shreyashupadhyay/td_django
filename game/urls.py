from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/create-room/', views.create_room, name='create_room'),
    path('api/join-room/', views.join_room, name='join_room'),
    path('room/<str:room_code>/waiting/', views.waiting_room, name='waiting_room'),
    path('room/<str:room_code>/game/', views.game_screen, name='game_screen'),
    path('api/room/<str:room_code>/choose/', views.choose_truth_dare, name='choose_truth_dare'),
    path('api/room/<str:room_code>/answer/', views.submit_answer, name='submit_answer'),
    path('api/room/<str:room_code>/next-round/', views.next_round, name='next_round'),
    path('api/room/<str:room_code>/start-game/', views.start_game, name='start_game'),
    path('api/room/<str:room_code>/status/', views.room_status, name='room_status'),
    path('api/admin/room/<str:room_code>/inject-question/', views.admin_inject_question, name='admin_inject_question'),
    path('standalone/', views.standalone_page, name='standalone_page'),
    path('api/standalone/request/', views.request_standalone_question, name='request_standalone_question'),
    path('api/standalone/<str:session_id>/status/', views.get_standalone_status, name='get_standalone_status'),
    path('api/admin/standalone/<str:session_id>/send-api/', views.admin_send_api_question, name='admin_send_api_question'),
    path('api/admin/standalone/<str:session_id>/inject/', views.admin_inject_standalone_question, name='admin_inject_standalone_question'),
]
