# CaseCrawl Frontend

React-based dashboard for CaseCrawl - Westlaw Asia crawler.

## Features

- **Batch Upload**: CSV/Excel upload with validation preview
- **Monitoring Dashboard**: Real-time progress tracking with WebSocket
- **Disambiguation Interface**: Human-in-the-loop case selection
- **Real-time Updates**: WebSocket notifications for case status changes

## Tech Stack

- React 18+ with TypeScript
- TanStack Query (React Query) for server state
- React Router for navigation
- Tailwind CSS for styling
- Axios for HTTP requests
- date-fns for date formatting

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Page components
│   ├── BatchUpload.tsx
│   ├── Dashboard.tsx
│   └── Disambiguation.tsx
├── hooks/         # Custom React hooks
│   └── useWebSocket.ts
├── utils/         # Utility functions
│   └── api.ts
├── types/         # TypeScript types
│   └── index.ts
└── main.tsx       # Entry point
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

### Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## WebSocket Events

- `case_completed`: Case successfully downloaded
- `case_error`: Case processing failed
- `civil_procedure_detected`: Civil procedure case found
- `ambiguous_requires_selection`: Human disambiguation needed
- `batch_complete`: All cases processed
