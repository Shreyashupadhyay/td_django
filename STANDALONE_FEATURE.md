# Standalone Truth & Dare Feature

## Overview
A new standalone page where anyone can get individual Truth or Dare questions without needing to join a game. Admins can monitor these requests and inject custom questions in real-time.

## Features

### For Users
1. **Access the Page**: Go to `/standalone/` or click "Get Single Question" on the home page
2. **Enter Name**: Provide your name to get started
3. **Choose Truth or Dare**: Select which type of question you want
4. **Get Question**: Receive a question from the API
5. **Get More**: Request as many questions as you want
6. **Admin Questions**: Receive custom questions injected by admins in real-time

### For Admins
1. **Monitor Requests**: View all active standalone requests in the admin dashboard
2. **See User Details**: Track who is requesting questions and when
3. **Inject Questions**: Send custom questions to specific users
4. **Real-time Updates**: Questions are delivered instantly via WebSocket

## How It Works

### User Flow
```
1. User visits /standalone/
2. Enters their name
3. Chooses Truth or Dare
4. Gets question from API (or admin)
5. Can request more questions
6. Session tracked via unique session_id
```

### Admin Flow
```
1. Admin logs into /admin/dashboard/
2. Views "Standalone Question Requests" section
3. Sees active users with their current questions
4. Clicks "Inject Question" button
5. Enters custom question and type
6. Question sent to user in real-time
```

## Technical Details

### New Model: `StandaloneRequest`
- `session_id`: Unique UUID for each user session
- `user_name`: User's display name
- `question_type`: 'truth' or 'dare'
- `current_question`: The current question text
- `question_source`: 'API' or 'ADMIN'
- `is_active`: Active status
- `created_at`, `updated_at`: Timestamps

### New Endpoints
- `GET /standalone/` - Standalone question page
- `POST /api/standalone/request/` - Request a new question
- `GET /api/standalone/<session_id>/status/` - Get session status
- `POST /api/admin/standalone/<session_id>/inject/` - Admin inject question (requires login)

### WebSocket Support
- Real-time question delivery from admin to user
- WebSocket URL: `ws://localhost:8000/ws/standalone/<session_id>/`
- Falls back gracefully if WebSocket unavailable

### Admin Dashboard Updates
- New section showing standalone requests
- Table displays: User name, question type, current question, source, last updated
- "Inject Question" button for each active request
- Separate modal for standalone question injection

## UI Components

### Standalone Page (`/standalone/`)
- Name input section
- Truth/Dare choice buttons
- Question display card
- "Get Another Question" button
- "Start Over" button
- Link back to game mode

### Admin Dashboard
- Standalone requests table (separate from game rooms)
- Color-coded badges for question types and sources
- Real-time timestamp updates
- Modal form for question injection

## Usage Examples

### User Example
```
1. Go to http://127.0.0.1:8000/standalone/
2. Enter name: "John"
3. Click "Truth"
4. See question: "What's your biggest secret?"
5. Click "Get Another Question"
6. Choose "Dare"
7. See question: "Do 20 push-ups"
```

### Admin Example
```
1. Go to http://127.0.0.1:8000/admin/dashboard/
2. See John in the Standalone Requests table
3. Click "Inject Question" next to John
4. Type: "What would you do with $1 million?"
5. Select type: Truth
6. Click "Inject Question"
7. John sees the new question instantly
```

## Benefits

1. **No Game Required**: Users can get questions without finding a partner
2. **Admin Control**: Full monitoring and custom question injection
3. **Real-time**: WebSocket enables instant question delivery
4. **Persistent Sessions**: Session tracked via UUID
5. **Standalone**: Completely separate from game rooms
6. **Scalable**: Multiple users can request questions simultaneously

## Notes

- WebSocket connection is optional - page works without it
- Admin must be logged in to inject questions
- Sessions are tracked by UUID, not cookies
- Users can change their name and start over anytime
- Questions from API are fetched with rate limiting
- Admin questions override API questions for that request
