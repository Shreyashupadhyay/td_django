# How to Play Truth & Dare

## Complete Game Flow

### Step 1: Start a Game
1. Open the website (http://127.0.0.1:8000/)
2. Click **"Start Game"**
3. Enter your name
4. You'll get a **Room Code** (e.g., "ABC123")
5. Share this code with your friend

### Step 2: Join a Game
1. Your friend opens the website
2. Clicks **"Join Game"**
3. Enters the **Room Code** you shared
4. Enters their name
5. Both players are now in the **Waiting Room**

### Step 3: Start the Game
- When 2 players join, a **"Start Game"** button appears
- Either player can click it to begin
- The game automatically redirects to the **Game Screen**

### Step 4: Play the Game

#### Turn-Based Gameplay:
1. **Player 1's Turn:**
   - Player 1 sees "It's YOUR turn!"
   - Player 1 chooses **Truth** or **Dare**
   - A question appears from the API
   - Player 1 types their answer and submits

2. **Player 2's Turn:**
   - Turn automatically switches to Player 2
   - Player 2 sees "It's YOUR turn!"
   - Player 2 chooses **Truth** or **Dare**
   - A question appears
   - Player 2 types their answer and submits

3. **Round Progression:**
   - After Player 2 answers, Round 2 begins
   - Player 1 goes first again
   - Game continues with alternating turns

## Game Features

### Truth Questions
- Personal questions about yourself
- Answer honestly!

### Dare Challenges
- Actions or tasks to complete
- Complete the dare!

### Admin Features
- Admins can inject custom questions
- Access admin dashboard at `/admin/dashboard/`
- Login required

## Troubleshooting

### If WebSocket Errors Appear:
- This is normal if using `runserver` instead of `daphne`
- The game will still work with polling fallback
- Refresh the page if stuck

### If Game Doesn't Start:
1. Make sure both players have joined
2. Click the "Start Game" button
3. Refresh the page if needed
4. Check browser console for errors

### If Stuck on "Waiting for game to start":
1. Refresh the page - game should auto-start
2. If button appears, click "Start Game"
3. The page polls every 3 seconds to update

## Technical Notes

- **WebSocket**: For real-time updates (requires `daphne` server)
- **Polling**: Fallback mechanism when WebSocket fails
- **Auto-start**: Game initializes when 2 players join
- **Turn Management**: Strictly turn-based, no skipping

## Server Setup

For full WebSocket support:
```bash
daphne -b 127.0.0.1 -p 8000 truth_dare.asgi:application
```

For basic functionality (without WebSockets):
```bash
python manage.py runserver
```
