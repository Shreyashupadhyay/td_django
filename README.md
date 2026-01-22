# Truth & Dare Web Application

A complete turn-based Truth & Dare web application built with Django, featuring real-time updates via WebSockets, external API integration, and an admin panel for question injection.

## Features

- **Room-based Gameplay**: Create or join rooms with unique codes
- **Turn-based Logic**: Strict turn-based gameplay between 2 players
- **Real-time Updates**: WebSocket-powered real-time game state updates
- **External API Integration**: Fetches Truth/Dare questions from external API
- **Admin Question Injection**: Admin can inject custom questions into active games
- **Modern UI**: Bootstrap-based responsive interface

## Tech Stack

### Backend
- Django 4.2+
- Django REST Framework
- Django Channels (WebSockets)
- SQLite (development)

### Frontend
- Django Templates (HTML)
- Bootstrap 5
- Vanilla JavaScript
- WebSocket API

### Authentication
- Simple username-based player identity (no password)
- Django Admin authentication for admin portal

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd TD
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (for admin access)**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin account.

7. **Run the development server**
   
   **IMPORTANT:** For WebSocket support, use Daphne instead of runserver:
   ```bash
   daphne -b 127.0.0.1 -p 8000 truth_dare.asgi:application
   ```
   
   Or alternatively, you can use:
   ```bash
   python manage.py runserver
   ```
   (Note: WebSockets won't work with runserver - use Daphne for full functionality)

8. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Admin dashboard: http://127.0.0.1:8000/admin/dashboard/ (requires login)

## Configuration

### External API Configuration

The application uses an external Truth & Dare API. Configure it in `truth_dare/settings.py`:

```python
TRUTH_DARE_API_BASE_URL = 'https://api.truthordarebot.xyz/v1'
TRUTH_DARE_API_RATING = 'pg'  # Options: pg, pg13, r
TRUTH_DARE_API_RATE_LIMIT_REQUESTS = 5
TRUTH_DARE_API_RATE_LIMIT_SECONDS = 5
```

You can also set these via environment variables:
- `TRUTH_DARE_API_BASE_URL`
- `TRUTH_DARE_API_RATING`

### Room Configuration

```python
ROOM_CODE_LENGTH = 6
ROOM_EXPIRY_HOURS = 24
```

## Usage

### For Players

1. **Start a Game**
   - Click "Start Game" on the home page
   - Enter your name
   - Share the room code with a friend

2. **Join a Game**
   - Click "Join Game" on the home page
   - Enter the room code and your name
   - Wait for the game to start (requires 2 players)

3. **Play the Game**
   - When it's your turn, choose "Truth" or "Dare"
   - Answer the question or complete the dare
   - Submit your answer to switch turns

### For Admins

1. **Access Admin Dashboard**
   - Log in at http://127.0.0.1:8000/admin/
   - Navigate to "Admin Dashboard" from the navbar

2. **View Active Rooms**
   - See all active rooms with player information
   - View current round and current player

3. **Inject Questions**
   - Click "Inject Question" for any active room
   - Enter a custom question text
   - Select question type (Truth or Dare)
   - The question will immediately appear in the game

## Project Structure

```
TD/
├── manage.py
├── requirements.txt
├── README.md
├── truth_dare/          # Main Django project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py          # ASGI config for WebSockets
├── game/                # Main game app
│   ├── models.py        # Database models
│   ├── views.py         # HTTP views
│   ├── urls.py          # URL routing
│   ├── consumers.py     # WebSocket consumers
│   ├── routing.py       # WebSocket routing
│   ├── services.py      # Business logic & API integration
│   ├── utils.py         # Utility functions
│   └── admin.py         # Admin configuration
├── templates/           # HTML templates
│   ├── base.html
│   └── game/
│       ├── home.html
│       ├── waiting_room.html
│       ├── game_screen.html
│       └── admin_dashboard.html
└── static/              # Static files
    └── admin/
        └── js/
            └── inject_question.js
```

## Database Models

- **Room**: Game rooms with unique codes
- **Player**: Players in rooms
- **GameState**: Current game state (turn, round, etc.)
- **Question**: Questions (from API or admin)
- **Answer**: Player answers to questions

## WebSocket Events

- `join_room`: Player joins a room
- `start_game`: Game starts (2 players joined)
- `choose_truth_dare`: Player chooses Truth or Dare
- `question_sent`: Question is displayed
- `submit_answer`: Answer is submitted
- `admin_question_injected`: Admin injects a question
- `room_state`: Current room state update

## API Endpoints

### Player Endpoints
- `POST /api/create-room/`: Create a new room
- `POST /api/join-room/`: Join an existing room
- `POST /api/room/<code>/choose/`: Choose Truth or Dare
- `POST /api/room/<code>/answer/`: Submit an answer

### Admin Endpoints
- `GET /admin/dashboard/`: Admin dashboard (requires login)
- `POST /api/admin/room/<code>/inject-question/`: Inject a question (requires login)

## Development Notes

- The application uses Django Channels with InMemoryChannelLayer for development
- For production, consider using Redis as the channel layer
- WebSocket connections automatically reconnect on disconnect
- Questions are cached per round to avoid duplicate API calls
- Rate limiting is implemented for API calls (5 requests per 5 seconds)

## Troubleshooting

### WebSocket Connection Issues
- Ensure Django Channels is properly installed
- Check that ASGI application is configured correctly
- Verify WebSocket URL patterns in `game/routing.py`

### API Integration Issues
- Check API base URL in settings
- Verify network connectivity
- Check API rate limits
- Fallback questions are used if API fails

### Database Issues
- Run `python manage.py migrate` to apply migrations
- Check SQLite database file permissions
- Verify database path in settings.py

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Update `SECRET_KEY` with a secure random key
3. Configure proper `ALLOWED_HOSTS`
4. Use a production database (PostgreSQL recommended)
5. Configure Redis for channel layers
6. Set up proper static file serving
7. Use a production ASGI server (Daphne or Uvicorn)
8. Configure HTTPS for WebSocket connections

## License

This project is provided as-is for educational and development purposes.

## Support

For issues or questions, please check:
- Django Channels documentation: https://channels.readthedocs.io/
- Django documentation: https://docs.djangoproject.com/
