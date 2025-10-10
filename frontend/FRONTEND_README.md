# nQuiry React Frontend

A modern React frontend for the nQuiry Intelligent Query Assistant, built to replace the Streamlit interface while maintaining all functionality.

## Features

✅ **Complete Streamlit Functionality Replicated:**
- Customer email authentication with query processor initialization
- Real-time chat interface with message history
- Voice input support using Web Speech API
- Comprehensive ticket creation system with all Streamlit form fields
- Sidebar with conversation history and system status
- Audio feedback toggle
- Professional UI that matches Streamlit styling

✅ **Enhanced React Features:**
- Modern component architecture
- Responsive design with Tailwind CSS
- Smooth animations and transitions
- Copy message functionality
- Auto-scroll chat container
- Loading states and error handling
- Voice recording indicators

## Components Overview

### Core Components
- **App.jsx** - Main application with state management
- **Header.jsx** - Top navigation with user info
- **AuthenticationForm.jsx** - Customer email authentication
- **ChatContainer.jsx** - Message display area
- **ChatInputFixed.jsx** - Input field with voice support
- **ChatMessage.jsx** - Individual message component
- **Sidebar.jsx** - Chat history and system status
- **TicketForm.jsx** - Support ticket creation

### Services
- **api.js** - Axios configuration with interceptors
- **chatService.js** - API service layer for all backend calls

### Utilities
- **constants.js** - App constants and configuration
- **globals.css** - Tailwind CSS styles and animations

## Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

## Backend Integration

The frontend connects to a FastAPI backend at `http://127.0.0.1:8000/api` with endpoints:

- `POST /chat/initialize` - Initialize query processor
- `POST /chat` - Send chat messages
- `GET /chat/history/{user_id}` - Get conversation history
- `DELETE /chat/history/{user_id}` - Clear chat history
- `POST /tickets/create` - Create support tickets
- `GET /users` - Get user information

## Key Features Replicated from Streamlit

### Authentication Flow
- Email-based customer authentication
- Role-based access initialization
- Error handling for failed initialization

### Chat Interface
- Message bubbles with proper styling
- Timestamps and user indicators
- Markdown formatting support
- Real-time message display

### Voice Input
- Web Speech API integration
- Visual recording indicators
- Fallback for unsupported browsers
- Voice command processing

### Ticket Creation
- All form fields from Streamlit:
  - Priority selection
  - Area affected
  - Version affected
  - Environment selection
  - Auto-generated description from conversation
- Escalation vs regular ticket support
- Success confirmation with ticket IDs

### Sidebar Features
- System status indicators (nQuiry, JIRA, MindTouch)
- Conversation history with timestamps
- New conversation button
- Clear history functionality
- Audio feedback toggle

## Styling

The UI uses Tailwind CSS with custom components that match the Streamlit interface:
- Professional blue and green color scheme
- Smooth animations and transitions
- Responsive design for all screen sizes
- Modern glassmorphism effects
- Consistent spacing and typography

## Browser Support

- **Voice Input**: Chrome, Edge, Safari (with Web Speech API)
- **General Usage**: All modern browsers
- **Responsive**: Mobile and desktop

## Development Notes

- Built with React 18 and Vite
- Uses Axios for API communication
- Tailwind CSS for styling
- Lucide React for icons
- Fully typed props and state management

The React frontend provides a seamless replacement for Streamlit with enhanced user experience and modern web technologies.