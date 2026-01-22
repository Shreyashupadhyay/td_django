import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Player, GameState, Question
from .services import TurnManagementService


class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time game updates."""
    
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_{self.room_code}'
        
        # Check if room exists
        room = await self.get_room()
        if not room:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current room state
        await self.send_room_state()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            event_type = data.get('type')
            
            if event_type == 'join_room':
                await self.handle_join_room(data)
            elif event_type == 'start_game':
                await self.handle_start_game()
            elif event_type == 'choose_truth_dare':
                await self.handle_choose_truth_dare(data)
            elif event_type == 'submit_answer':
                await self.handle_submit_answer(data)
            elif event_type == 'get_state':
                await self.send_room_state()
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_join_room(self, data):
        """Handle player joining room."""
        room = await self.get_room()
        if room:
            # Check if room is now full and game should start
            if room.is_full():
                # Initialize game if not already started
                existing_game_state = await self.get_game_state(room)
                if not existing_game_state:
                    await self.handle_start_game()
            
            await self.send_room_state()
            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_joined',
                    'room_code': self.room_code
                }
            )
    
    async def handle_start_game(self):
        """Handle game start."""
        room = await self.get_room()
        if room and room.is_full():
            game_state = await database_sync_to_async(TurnManagementService.initialize_game)(room)
            if game_state:
                await self.send_room_state()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_started',
                        'room_code': self.room_code
                    }
                )
    
    async def handle_choose_truth_dare(self, data):
        """Handle truth/dare choice."""
        player_id = data.get('player_id')
        choice = data.get('choice')
        
        room = await self.get_room()
        if not room:
            return
        
        player = await self.get_player(player_id)
        if not player:
            return
        
        game_state = await self.get_game_state(room)
        if not game_state or game_state.current_turn_player_id != player.id:
            return
        
        # Update game state
        game_state.current_choice = choice
        game_state.is_waiting_for_question = True
        await database_sync_to_async(game_state.save)()
        
        # Create question
        question = await database_sync_to_async(
            TurnManagementService.create_question_from_api
        )(room, choice)
        
        if question:
            await self.send_room_state()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'question_sent',
                    'room_code': self.room_code,
                    'question': {
                        'id': question.id,
                        'text': question.text,
                        'type': question.question_type,
                        'source': question.source
                    }
                }
            )
    
    async def handle_submit_answer(self, data):
        """Handle answer submission."""
        player_id = data.get('player_id')
        answer_text = data.get('answer_text')
        
        room = await self.get_room()
        if not room:
            return
        
        player = await self.get_player(player_id)
        if not player:
            return
        
        answer = await database_sync_to_async(
            TurnManagementService.submit_answer
        )(room, player, answer_text)
        
        if answer:
            await self.send_room_state()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'answer_submitted',
                    'room_code': self.room_code,
                    'next_turn': answer.question.game_state.current_turn_player.name if answer.question.game_state.current_turn_player else None
                }
            )
    
    async def send_room_state(self):
        """Send current room state to client."""
        room = await self.get_room()
        if not room:
            return
        
        players_data = []
        for player in await self.get_players(room):
            players_data.append({
                'id': player.id,
                'name': player.name,
                'join_order': player.join_order
            })
        
        game_state = await self.get_game_state(room)
        game_state_data = None
        current_question = None
        
        if game_state:
            current_player = await self.get_player(game_state.current_turn_player_id) if game_state.current_turn_player_id else None
            game_state_data = {
                'round_number': game_state.round_number,
                'current_turn_player_id': game_state.current_turn_player_id,
                'current_turn_player_name': current_player.name if current_player else None,
                'current_choice': game_state.current_choice,
                'is_waiting_for_question': game_state.is_waiting_for_question,
                'is_waiting_for_answer': game_state.is_waiting_for_answer
            }
            
            question = await self.get_current_question(room)
            if question:
                current_question = {
                    'id': question.id,
                    'text': question.text,
                    'type': question.question_type,
                    'source': question.source
                }
        
        await self.send(text_data=json.dumps({
            'type': 'room_state',
            'room': {
                'code': room.code,
                'is_active': room.is_active,
                'is_full': room.is_full()
            },
            'players': players_data,
            'game_state': game_state_data,
            'current_question': current_question
        }))
    
    # WebSocket event handlers
    async def player_joined(self, event):
        """Handle player joined event."""
        await self.send_room_state()
    
    async def game_started(self, event):
        """Handle game started event."""
        await self.send_room_state()
    
    async def question_sent(self, event):
        """Handle question sent event."""
        await self.send(text_data=json.dumps({
            'type': 'question_sent',
            'question': event['question']
        }))
    
    async def answer_submitted(self, event):
        """Handle answer submitted event."""
        await self.send(text_data=json.dumps({
            'type': 'answer_submitted',
            'next_turn': event.get('next_turn')
        }))
    
    async def admin_question_injected(self, event):
        """Handle admin question injection."""
        await self.send(text_data=json.dumps({
            'type': 'admin_question_injected',
            'question': event['question']
        }))
        await self.send_room_state()
    
    # Database helpers
    @database_sync_to_async
    def get_room(self):
        try:
            room = Room.objects.get(code=self.room_code, is_active=True)
            # Refresh players count
            room.refresh_from_db()
            return room
        except Room.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_player(self, player_id):
        try:
            return Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_players(self, room):
        return list(room.get_players())
    
    @database_sync_to_async
    def get_game_state(self, room):
        return room.get_current_game_state()
    
    @database_sync_to_async
    def get_current_question(self, room):
        return TurnManagementService.get_current_question(room)


class StandaloneConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for standalone truth/dare requests."""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'standalone_{self.session_id}'
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            # Handle any client messages if needed
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def admin_question_injected(self, event):
        """Handle admin question injection."""
        await self.send(text_data=json.dumps({
            'type': 'admin_question_injected',
            'question': event['question']
        }))
