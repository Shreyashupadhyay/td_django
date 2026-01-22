"""
Service layer for game logic and external API integration.
"""
import requests
import time
from django.conf import settings
from django.core.cache import cache
from .models import Room, Player, GameState, Question, Answer


class APIQuestionService:
    """Service for fetching questions from external API."""
    
    def __init__(self):
        self.base_url = settings.TRUTH_DARE_API_BASE_URL
        self.rating = settings.TRUTH_DARE_API_RATING
        self.rate_limit_requests = settings.TRUTH_DARE_API_RATE_LIMIT_REQUESTS
        self.rate_limit_seconds = settings.TRUTH_DARE_API_RATE_LIMIT_SECONDS
        self.request_times = []
    
    def _check_rate_limit(self):
        """Check if we're within rate limit."""
        current_time = time.time()
        # Remove requests older than rate_limit_seconds
        self.request_times = [t for t in self.request_times if current_time - t < self.rate_limit_seconds]
        
        if len(self.request_times) >= self.rate_limit_requests:
            return False
        return True
    
    def _record_request(self):
        """Record a request timestamp."""
        self.request_times.append(time.time())
    
    def fetch_truth_question(self):
        """Fetch a truth question from the API."""
        if not self._check_rate_limit():
            # Return a fallback question if rate limited
            return {
                'id': 'fallback',
                'type': 'truth',
                'rating': self.rating,
                'question': 'What is your biggest fear?'
            }
        
        try:
            url = f"{self.base_url}/truth"
            params = {'rating': self.rating} if self.rating else {}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            self._record_request()
            return data
        except Exception as e:
            # Return fallback on error
            return {
                'id': 'fallback',
                'type': 'truth',
                'rating': self.rating,
                'question': 'What is your biggest fear?'
            }
    
    def fetch_dare_question(self):
        """Fetch a dare question from the API."""
        if not self._check_rate_limit():
            # Return a fallback question if rate limited
            return {
                'id': 'fallback',
                'type': 'dare',
                'rating': self.rating,
                'question': 'Do 10 jumping jacks.'
            }
        
        try:
            # Try /api/dare first, then fallback to /dare
            urls = [f"{self.base_url}/api/dare", f"{self.base_url}/dare"]
            params = {'rating': self.rating} if self.rating else {}
            
            for url in urls:
                try:
                    response = requests.get(url, params=params, timeout=5)
                    response.raise_for_status()
                    data = response.json()
                    self._record_request()
                    return data
                except:
                    continue
            
            # If all URLs fail, raise exception
            raise Exception("All API endpoints failed")
        except Exception as e:
            # Return fallback on error
            return {
                'id': 'fallback',
                'type': 'dare',
                'rating': self.rating,
                'question': 'Do 10 jumping jacks.'
            }


class TurnManagementService:
    """Service for managing game turns and flow."""
    
    @staticmethod
    def initialize_game(room):
        """Initialize game state when 2 players join."""
        players = list(room.get_players())
        if len(players) != 2:
            return None
        
        # Check if game state already exists
        existing_game_state = room.get_current_game_state()
        if existing_game_state:
            return existing_game_state
        
        game_state = GameState.objects.create(
            room=room,
            current_turn_player=players[0],
            round_number=1
        )
        return game_state
    
    @staticmethod
    def get_current_question(room):
        """Get the current unanswered question for the room."""
        game_state = room.get_current_game_state()
        if not game_state:
            return None
        
        return Question.objects.filter(
            game_state=game_state,
            is_answered=False
        ).first()
    
    @staticmethod
    def create_question_from_api(room, question_type):
        """Create a question from API for the current round."""
        game_state = room.get_current_game_state()
        if not game_state:
            return None
        
        api_service = APIQuestionService()
        
        if question_type == 'truth':
            api_data = api_service.fetch_truth_question()
        else:
            api_data = api_service.fetch_dare_question()
        
        question = Question.objects.create(
            room=room,
            game_state=game_state,
            text=api_data.get('question', 'No question available'),
            question_type=question_type,
            source='API'
        )
        
        return question
    
    @staticmethod
    def create_admin_question(room, question_text, question_type):
        """Create an admin-injected question."""
        game_state = room.get_current_game_state()
        if not game_state:
            return None
        
        # Mark any existing unanswered question as answered
        Question.objects.filter(
            game_state=game_state,
            is_answered=False
        ).update(is_answered=True)
        
        question = Question.objects.create(
            room=room,
            game_state=game_state,
            text=question_text,
            question_type=question_type,
            source='ADMIN'
        )
        
        return question
    
    @staticmethod
    def submit_answer(room, player, answer_text):
        """Submit an answer to the current question."""
        game_state = room.get_current_game_state()
        if not game_state:
            return None
        
        question = TurnManagementService.get_current_question(room)
        if not question:
            return None
        
        answer = Answer.objects.create(
            question=question,
            player=player,
            answer_text=answer_text
        )
        
        question.is_answered = True
        question.save()
        
        # Don't switch turn automatically - wait for next round button
        game_state.is_waiting_for_answer = False
        game_state.save()
        
        return answer
    
    @staticmethod
    def next_round(room):
        """Move to the next round after viewing the answer."""
        game_state = room.get_current_game_state()
        if not game_state:
            return None
        
        # Switch turn to next player
        game_state.switch_turn()
        game_state.is_waiting_for_question = False
        game_state.current_choice = None
        game_state.save()
        
        return game_state
