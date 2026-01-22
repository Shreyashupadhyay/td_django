from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
import uuid
from .models import Room, Player, GameState, Question, Answer, StandaloneRequest
from .services import TurnManagementService, APIQuestionService
from .utils import broadcast_admin_question, broadcast_standalone_question


@ensure_csrf_cookie
def home(request):
    """Home page with start game and join game options."""
    return render(request, 'game/home.html')


@require_http_methods(["POST"])
def create_room(request):
    """Create a new game room."""
    player_name = request.POST.get('player_name', '').strip()
    if not player_name:
        return JsonResponse({'error': 'Player name is required'}, status=400)
    
    room = Room.objects.create(created_by=player_name)
    player = Player.objects.create(
        name=player_name,
        room=room,
        join_order=1
    )
    
    return JsonResponse({
        'room_code': room.code,
        'player_id': player.id
    })


@require_http_methods(["POST"])
def join_room(request):
    """Join an existing room."""
    room_code = request.POST.get('room_code', '').strip().upper()
    player_name = request.POST.get('player_name', '').strip()
    
    if not room_code or not player_name:
        return JsonResponse({'error': 'Room code and player name are required'}, status=400)
    
    try:
        room = Room.objects.get(code=room_code, is_active=True)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found or inactive'}, status=404)
    
    if room.players.filter(name=player_name).exists():
        return JsonResponse({'error': 'Player name already taken in this room'}, status=400)
    
    if room.is_full():
        return JsonResponse({'error': 'Room is full'}, status=400)
    
    player = Player.objects.create(
        name=player_name,
        room=room,
        join_order=room.players.count() + 1
    )
    
    return JsonResponse({
        'room_code': room.code,
        'player_id': player.id
    })


def waiting_room(request, room_code):
    """Waiting room page."""
    room = get_object_or_404(Room, code=room_code.upper())
    players = room.get_players()
    player_id = request.GET.get('player_id')
    
    context = {
        'room': room,
        'players': players,
        'player_id': player_id,
        'is_full': room.is_full()
    }
    return render(request, 'game/waiting_room.html', context)


@ensure_csrf_cookie
def game_screen(request, room_code):
    """Main game screen."""
    room = get_object_or_404(Room, code=room_code.upper())
    player_id = request.GET.get('player_id')
    
    if not player_id:
        return redirect('home')
    
    try:
        player = Player.objects.get(id=player_id, room=room)
    except Player.DoesNotExist:
        return redirect('home')
    
    # Auto-start game if 2 players joined but game hasn't started
    game_state = room.get_current_game_state()
    if not game_state and room.is_full():
        game_state = TurnManagementService.initialize_game(room)
    
    current_question = TurnManagementService.get_current_question(room)
    
    context = {
        'room': room,
        'player': player,
        'game_state': game_state,
        'current_question': current_question,
        'is_my_turn': game_state and game_state.current_turn_player == player if game_state else False,
        'needs_start': room.is_full() and not game_state,
    }
    return render(request, 'game/game_screen.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def choose_truth_dare(request, room_code):
    """Handle truth/dare choice."""
    room = get_object_or_404(Room, code=room_code.upper())
    player_id = request.POST.get('player_id')
    choice = request.POST.get('choice')  # 'truth' or 'dare'
    
    if not player_id or choice not in ['truth', 'dare']:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        player = Player.objects.get(id=player_id, room=room)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    
    game_state = room.get_current_game_state()
    if not game_state or game_state.current_turn_player != player:
        return JsonResponse({'error': 'Not your turn'}, status=400)
    
    game_state.current_choice = choice
    game_state.is_waiting_for_question = True
    game_state.save()
    
    # Create question from API
    question = TurnManagementService.create_question_from_api(room, choice)
    
    if question:
        return JsonResponse({
            'success': True,
            'question': {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'source': question.source
            }
        })
    
    return JsonResponse({'error': 'Failed to fetch question'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def submit_answer(request, room_code):
    """Submit answer to current question."""
    room = get_object_or_404(Room, code=room_code.upper())
    player_id = request.POST.get('player_id')
    answer_text = request.POST.get('answer_text', '').strip()
    
    if not player_id or not answer_text:
        return JsonResponse({'error': 'Player ID and answer text are required'}, status=400)
    
    try:
        player = Player.objects.get(id=player_id, room=room)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    
    game_state = room.get_current_game_state()
    if not game_state or game_state.current_turn_player != player:
        return JsonResponse({'error': 'Not your turn'}, status=400)
    
    answer = TurnManagementService.submit_answer(room, player, answer_text)
    
    if answer:
        return JsonResponse({
            'success': True,
            'next_turn': game_state.current_turn_player.name if game_state.current_turn_player else None,
            'round_number': game_state.round_number
        })
    
    return JsonResponse({'error': 'Failed to submit answer'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def start_game(request, room_code):
    """Manually start the game when 2 players have joined."""
    room = get_object_or_404(Room, code=room_code.upper())
    
    # Try to get player_id from POST or JSON body
    player_id = None
    if request.POST.get('player_id'):
        player_id = request.POST.get('player_id')
    elif request.body:
        try:
            body_data = json.loads(request.body)
            player_id = body_data.get('player_id')
        except:
            pass
    
    if not room.is_full():
        return JsonResponse({'error': 'Room is not full yet'}, status=400)
    
    # Initialize game if not already started
    game_state = room.get_current_game_state()
    if not game_state:
        game_state = TurnManagementService.initialize_game(room)
        if not game_state:
            return JsonResponse({'error': 'Failed to initialize game'}, status=500)
    
    return JsonResponse({
        'success': True,
        'game_started': True,
        'room_code': room.code
    })


@require_http_methods(["GET"])
def room_status(request, room_code):
    """Get current room status."""
    room = get_object_or_404(Room, code=room_code.upper())
    game_state = room.get_current_game_state()
    
    players_data = []
    for player in room.get_players():
        players_data.append({
            'id': player.id,
            'name': player.name,
            'join_order': player.join_order
        })
    
    # Get current question if exists
    current_question = None
    current_answer = None
    if game_state:
        question = TurnManagementService.get_current_question(room)
        if not question:
            # Check for the most recent answered question
            question = Question.objects.filter(
                game_state=game_state,
                is_answered=True
            ).first()
        
        if question:
            current_question = {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'source': question.source,
                'is_answered': question.is_answered
            }
            
            # Get the answer if it exists
            answer = question.answers.first()
            if answer:
                current_answer = {
                    'id': answer.id,
                    'text': answer.answer_text,
                    'player_name': answer.player.name,
                    'player_id': answer.player.id
                }
    
    return JsonResponse({
        'room_code': room.code,
        'is_full': room.is_full(),
        'is_active': room.is_active,
        'game_started': game_state is not None,
        'players': players_data,
        'round_number': game_state.round_number if game_state else None,
        'current_turn_player': game_state.current_turn_player.name if game_state and game_state.current_turn_player else None,
        'current_turn_player_id': game_state.current_turn_player.id if game_state and game_state.current_turn_player else None,
        'current_question': current_question,
        'current_answer': current_answer,
        'is_waiting_for_question': game_state.is_waiting_for_question if game_state else False,
        'is_waiting_for_answer': game_state.is_waiting_for_answer if game_state else False
    })


@ensure_csrf_cookie
def standalone_page(request):
    """Standalone truth/dare question page."""
    return render(request, 'game/standalone.html')


@require_http_methods(["POST"])
@csrf_exempt
def request_standalone_question(request):
    """Request a truth/dare question (standalone, not in a game) - puts user on hold for admin."""
    user_name = request.POST.get('user_name', '').strip()
    question_type = request.POST.get('question_type', '').strip()
    session_id = request.POST.get('session_id', '').strip()
    
    if not user_name or question_type not in ['truth', 'dare']:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Get or create standalone request
    standalone_request, created = StandaloneRequest.objects.get_or_create(
        session_id=session_id,
        defaults={
            'user_name': user_name,
            'question_type': question_type,
            'status': 'PENDING',
            'is_active': True
        }
    )
    
    if not created:
        # Update existing request
        standalone_request.user_name = user_name
        standalone_request.question_type = question_type
        standalone_request.status = 'PENDING'
        standalone_request.current_question = None
        standalone_request.question_source = None
        standalone_request.is_active = True
        standalone_request.save()
    
    # User is now waiting for admin approval
    return JsonResponse({
        'success': True,
        'session_id': session_id,
        'status': 'PENDING',
        'message': 'Waiting for admin approval...'
    })


@require_http_methods(["GET"])
def get_standalone_status(request, session_id):
    """Get status of a standalone request."""
    try:
        standalone_request = StandaloneRequest.objects.get(session_id=session_id)
        return JsonResponse({
            'success': True,
            'user_name': standalone_request.user_name,
            'question_type': standalone_request.question_type,
            'current_question': standalone_request.current_question,
            'question_source': standalone_request.question_source,
            'status': standalone_request.status,
            'is_active': standalone_request.is_active
        })
    except StandaloneRequest.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)


@login_required
def admin_dashboard(request):
    """Admin dashboard for managing rooms and standalone requests."""
    active_rooms = Room.objects.filter(is_active=True).prefetch_related('players', 'game_states')
    # Show pending and recently approved requests
    standalone_requests = StandaloneRequest.objects.filter(
        is_active=True
    ).exclude(status='COMPLETED').order_by('-updated_at')
    return render(request, 'game/admin_dashboard.html', {
        'rooms': active_rooms,
        'standalone_requests': standalone_requests
    })


@require_http_methods(["POST"])
@csrf_exempt
def start_game(request, room_code):
    """Manually start the game when 2 players have joined."""
    room = get_object_or_404(Room, code=room_code.upper())
    player_id = request.POST.get('player_id') or request.body and json.loads(request.body).get('player_id')
    
    if not room.is_full():
        return JsonResponse({'error': 'Room is not full yet'}, status=400)
    
    # Initialize game if not already started
    game_state = room.get_current_game_state()
    if not game_state:
        game_state = TurnManagementService.initialize_game(room)
        if not game_state:
            return JsonResponse({'error': 'Failed to initialize game'}, status=500)
    
    return JsonResponse({
        'success': True,
        'game_started': True,
        'room_code': room.code
    })


@require_http_methods(["POST"])
@csrf_exempt
def next_round(request, room_code):
    """Move to next round after viewing answer."""
    room = get_object_or_404(Room, code=room_code.upper())
    
    game_state = TurnManagementService.next_round(room)
    
    if game_state:
        return JsonResponse({
            'success': True,
            'next_turn': game_state.current_turn_player.name if game_state.current_turn_player else None,
            'next_turn_id': game_state.current_turn_player.id if game_state.current_turn_player else None,
            'round_number': game_state.round_number
        })
    
    return JsonResponse({'error': 'Failed to move to next round'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def admin_inject_question(request, room_code):
    """Admin endpoint to inject a question."""
    room = get_object_or_404(Room, code=room_code.upper())
    question_text = request.POST.get('question_text', '').strip()
    question_type = request.POST.get('question_type', 'truth')
    
    if not question_text or question_type not in ['truth', 'dare']:
        return JsonResponse({'error': 'Invalid question data'}, status=400)
    
    question = TurnManagementService.create_admin_question(room, question_text, question_type)
    
    if question:
        # Broadcast to WebSocket clients
        question_data = {
            'id': question.id,
            'text': question.text,
            'type': question.question_type,
            'source': question.source
        }
        broadcast_admin_question(room_code.upper(), question_data)
        
        return JsonResponse({
            'success': True,
            'question': question_data
        })
    
    return JsonResponse({'error': 'Failed to inject question'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def admin_send_api_question(request, session_id):
    """Admin endpoint to approve request and send API question."""
    try:
        standalone_request = StandaloneRequest.objects.get(session_id=session_id)
    except StandaloneRequest.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    
    # Fetch question from API based on requested type
    api_service = APIQuestionService()
    question_type = standalone_request.question_type
    
    if question_type == 'truth':
        api_data = api_service.fetch_truth_question()
    else:
        api_data = api_service.fetch_dare_question()
    
    question_text = api_data.get('question', 'No question available')
    
    # Update standalone request with API question
    standalone_request.current_question = question_text
    standalone_request.question_source = 'API'
    standalone_request.status = 'APPROVED'
    standalone_request.save()
    
    # Broadcast to WebSocket clients
    question_data = {
        'text': question_text,
        'type': question_type,
        'source': 'API'
    }
    broadcast_standalone_question(session_id, question_data)
    
    return JsonResponse({
        'success': True,
        'question': question_data
    })


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def admin_inject_standalone_question(request, session_id):
    """Admin endpoint to inject a question to standalone user."""
    try:
        standalone_request = StandaloneRequest.objects.get(session_id=session_id)
    except StandaloneRequest.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    
    question_text = request.POST.get('question_text', '').strip()
    question_type = request.POST.get('question_type', 'truth')
    
    if not question_text or question_type not in ['truth', 'dare']:
        return JsonResponse({'error': 'Invalid question data'}, status=400)
    
    # Update standalone request with admin question
    standalone_request.current_question = question_text
    standalone_request.question_type = question_type
    standalone_request.question_source = 'ADMIN'
    standalone_request.status = 'APPROVED'
    standalone_request.save()
    
    # Broadcast to WebSocket clients
    question_data = {
        'text': question_text,
        'type': question_type,
        'source': 'ADMIN'
    }
    broadcast_standalone_question(session_id, question_data)
    
    return JsonResponse({
        'success': True,
        'question': question_data
    })
