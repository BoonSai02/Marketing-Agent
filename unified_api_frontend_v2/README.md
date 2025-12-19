# Unified API Frontend V2

A modern, clean frontend for the Unified API Marketing Agent built with Vite, React 19, and TypeScript.

## Features

- 🔐 **Complete Authentication System**
  - Email/password login and signup
  - Google OAuth integration
  - Email verification with OTP
  - Password reset flow
  - Protected routes

- 💬 **AI Chat Dashboard**
  - Multi-session management
  - Real-time messaging
  - Chat history
  - Auto-scroll to latest messages

- 🎨 **Beautiful UI**
  - Responsive design
  - Modern components
  - Smooth animations
  - Professional landing page

## Tech Stack

- **Vite 5.4** - Build tool
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Styling
- **Wouter** - Routing
- **Axios** - HTTP client
- **Sonner** - Toast notifications
- **React Hook Form + Zod** - Forms and validation

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/      # Reusable UI components
├── contexts/        # React contexts (Auth, Theme)
├── lib/             # Utilities (API client, helpers)
├── pages/           # Page components
│   ├── auth/        # Authentication pages
│   ├── Home.tsx     # Landing page
│   └── Dashboard.tsx # Chat interface
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Run TypeScript type checking

## API Integration

The app connects to the backend API at `VITE_API_URL`. Supported endpoints:

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password
- `GET /api/auth/google/login` - Google OAuth login
- `POST /api/agent/chat` - Send chat message

## Features

### Authentication
- Secure JWT-based authentication
- Token persistence in localStorage
- Auto-redirect on 401 errors
- Google OAuth integration

### Dashboard
- Create multiple chat sessions
- Switch between conversations
- Real-time message updates
- Loading states and error handling

### Responsive Design
- Mobile-first approach
- Works on all screen sizes
- Touch-friendly interface

## License

MIT
