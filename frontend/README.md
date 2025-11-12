# Attuned Survey - Frontend

React application for the Attuned intimacy profile survey.

**Version:** v0.6 (Compatibility Algorithm)  
**Last Updated:** November 12, 2025

## Tech Stack

- **React 18** with hooks
- **Vite** for fast development and building
- **React Router v6** for routing
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Lucide React** for icons

## Project Structure

```
src/
├── components/       # Reusable UI components
│   └── ui/          # shadcn/ui components
├── pages/           # Page components
│   ├── Landing.jsx  # Homepage
│   ├── Survey.jsx   # Survey flow
│   ├── Result.jsx   # Results display
│   ├── Privacy.jsx  # Privacy policy
│   └── Admin.jsx    # Admin panel
├── lib/             # Business logic
│   ├── scoring/     # Scoring algorithms
│   │   ├── profileCalculator.js    # Main profile calculator
│   │   ├── powerCalculator.js      # Power dynamics
│   │   ├── domainCalculator.js     # Domain scores
│   │   ├── activityConverter.js    # Activity key mapping
│   │   └── ...
│   ├── matching/    # Compatibility matching (v0.6)
│   │   ├── compatibilityMapper.js  # Asymmetric algorithm
│   │   └── categoryMap.js          # Activity display names
│   ├── storage/     # Data persistence
│   │   └── apiStore.js
│   └── surveyData.js # Survey data loader
├── data/            # Survey content
│   ├── schema.json  # Survey schema
│   └── questions.csv # Question bank
└── App.jsx          # Root component
```

## Development

### Install Dependencies
```bash
pnpm install
```

### Start Dev Server
```bash
pnpm run dev
```
Runs on http://localhost:5173

### Build for Production
```bash
pnpm run build
```
Output: `dist/`

### Preview Production Build
```bash
pnpm run preview
```

## Key Features

### Survey Flow
- Chapter-by-chapter navigation
- Real-time validation
- Progress tracking
- Session persistence (localStorage)

### Scoring Engine
- Trait calculation from raw answers
- Dial scores (4 dimensions)
- Archetype matching (top 3)
- Boundary extraction

### Compatibility Matching
- Category-by-category alignment
- Power complement detection
- Boundary gate checking
- Overall match score

### Admin Panel
- Password protected
- View all submissions
- Set baseline profile
- Export data (CSV/JSON)

## Configuration

### API Base URL
Edit `src/lib/storage/apiStore.js`:
```javascript
const API_BASE = '/api/survey'; // Change for different backend
```

### Brand Colors
Edit `src/App.css`:
```css
:root {
  --primary: 155 107 143;    /* Dusty Mauve */
  --secondary: 224 139 113;  /* Warm Coral */
  /* ... */
}
```

### Admin Password
Backend handles authentication. See `backend/src/routes/survey.py`.

## Components

### Pages

**Landing** - Homepage with survey introduction  
**Survey** - Multi-chapter survey with validation  
**Result** - Results display with archetypes and dials  
**Privacy** - Privacy policy  
**Admin** - Admin panel for data management

### UI Components (shadcn/ui)

- Button
- Input
- Card
- Progress
- Alert
- RadioGroup
- Table
- Label

## Styling

### Tailwind CSS
Utility-first CSS framework. Configure in `tailwind.config.js`.

### Custom Colors
Brand colors defined in `src/App.css` using CSS variables.

### Responsive Design
Mobile-first approach with breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

## Data Flow

1. User answers questions → `Survey.jsx`
2. Answers stored in state → `useState`
3. On submit → Calculate scores → `scoring/`
4. Save to API → `apiStore.saveSubmission()`
5. Navigate to results → `Result.jsx`
6. Load submission from API → Display results

## Testing

### Component Tests
```bash
pnpm run test
```

### E2E Tests
```bash
pnpm run test:e2e
```

## Deployment

### Build
```bash
pnpm run build
```

### Deploy to Vercel
```bash
vercel deploy
```

### Deploy with Backend
```bash
# Build frontend
pnpm run build

# Copy to backend static folder
cp -r dist/* ../backend/src/static/
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### API Connection Issues
Check `API_BASE` in `src/lib/storage/apiStore.js` matches backend URL.

## License

Proprietary. All rights reserved.

