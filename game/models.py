from django.db import models
from django.utils import timezone
import random
import string


def generate_room_code():
    """Generate a unique 6-character room code."""
    length = 6
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return code


class Room(models.Model):
    """Represents a game room."""
    code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        """Override save to generate unique room code if not provided."""
        if not self.code:
            # Generate unique code
            length = 6
            max_attempts = 100
            attempts = 0
            while attempts < max_attempts:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
                try:
                    if not Room.objects.filter(code=code).exists():
                        self.code = code
                        break
                except Exception:
                    # Table might not exist during migrations
                    self.code = code
                    break
                attempts += 1
            else:
                # Fallback if we can't generate unique code
                self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.code}"

    def get_players(self):
        """Get all players in this room."""
        return self.players.all().order_by('join_order')

    def get_current_game_state(self):
        """Get the current game state for this room."""
        return self.game_states.first()

    def is_full(self):
        """Check if room has 2 players."""
        return self.players.count() >= 2


class Player(models.Model):
    """Represents a player in a room."""
    name = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    join_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['join_order']
        unique_together = ['room', 'name']

    def __str__(self):
        return f"{self.name} in {self.room.code}"


class GameState(models.Model):
    """Tracks the current state of a game in a room."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='game_states')
    current_turn_player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True, related_name='current_turns')
    round_number = models.IntegerField(default=1)
    current_choice = models.CharField(max_length=10, null=True, blank=True)  # 'truth' or 'dare'
    is_waiting_for_question = models.BooleanField(default=False)
    is_waiting_for_answer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"GameState for {self.room.code} - Round {self.round_number}"

    def get_current_player(self):
        """Get the player whose turn it is."""
        return self.current_turn_player

    def get_opponent(self):
        """Get the opponent of the current player."""
        players = list(self.room.get_players())
        if len(players) == 2:
            return players[1] if self.current_turn_player == players[0] else players[0]
        return None

    def switch_turn(self):
        """Switch turn to the other player."""
        players = list(self.room.get_players())
        if len(players) == 2:
            if self.current_turn_player == players[0]:
                self.current_turn_player = players[1]
            else:
                self.current_turn_player = players[0]
                self.round_number += 1
            self.save()


class Question(models.Model):
    """Represents a question (truth or dare) in a game."""
    SOURCE_CHOICES = [
        ('API', 'API'),
        ('ADMIN', 'Admin'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='questions')
    game_state = models.ForeignKey(GameState, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10)  # 'truth' or 'dare'
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='API')
    created_at = models.DateTimeField(auto_now_add=True)
    is_answered = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.question_type.upper()} Question for {self.room.code}"


class Answer(models.Model):
    """Represents a player's answer to a question."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['question', 'player']

    def __str__(self):
        return f"Answer by {self.player.name} to question {self.question.id}"


class StandaloneRequest(models.Model):
    """Represents a standalone truth/dare request (not part of a game)."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Admin Approval'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True)
    user_name = models.CharField(max_length=100)
    question_type = models.CharField(max_length=10, null=True, blank=True)  # 'truth' or 'dare'
    current_question = models.TextField(null=True, blank=True)
    question_source = models.CharField(max_length=10, null=True, blank=True)  # 'API' or 'ADMIN'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Standalone request by {self.user_name} ({self.session_id})"
