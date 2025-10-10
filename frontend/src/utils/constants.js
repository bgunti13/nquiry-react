export const ORGANIZATIONS = [
  { name: 'AMD', email: 'support@amd.com', role: 'Customer' },
  { name: 'Viatris', email: 'support@viatris.com', role: 'Customer' },
  { name: 'Novartis', email: 'support@novartis.com', role: 'Customer' },
  { name: 'Wdc', email: 'support@wdc.com', role: 'Customer' },
]

export const EXAMPLE_QUERIES = [
  "What's the latest version of your software?",
  "How do I configure SSL certificates?",
  "What are the system requirements?",
  "How do I troubleshoot connection issues?",
  "What's included in the premium support plan?",
  "How do I upgrade my license?",
  "What's the difference between your product tiers?",
  "How do I integrate with third-party tools?",
  "What's your data retention policy?",
  "How do I set up automated backups?"
]

export const MESSAGE_TYPES = {
  USER: 'user',
  BOT: 'bot',
  SYSTEM: 'system'
}

export const API_ENDPOINTS = {
  CHAT: '/chat',
  CHAT_HISTORY: '/chat/history',
  INITIALIZE: '/chat/initialize',
  USERS: '/users',
  TICKETS: '/tickets'
}

export const VOICE_SETTINGS = {
  LANGUAGE: 'en-US',
  RATE: 1.0,
  PITCH: 1.0,
  VOLUME: 1.0
}

export const UI_CONFIG = {
  SIDEBAR_WIDTH: 320,
  MAX_MESSAGE_LENGTH: 1000,
  CHAT_SCROLL_BEHAVIOR: 'smooth',
  TYPING_INDICATOR_DELAY: 500
}