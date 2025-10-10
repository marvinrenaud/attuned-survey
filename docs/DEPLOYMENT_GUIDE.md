# Attuned Survey Website - Deployment Guide

## Overview

The **Attuned Intimacy Profile Survey** is a comprehensive web application built to help users discover their unique intimacy profile through a scientifically-designed questionnaire. The application implements the IntimacAI v0.2.3 survey framework with full scoring, matching, and data management capabilities.

## Deployment Status

✅ **Application Built Successfully**  
✅ **Ready for Production Deployment**

The application has been packaged and is awaiting your confirmation to publish to a public URL.

---

## Key Features Implemented

### 1. **Survey Flow**
- **5 Chapters** organized by theme:
  - Arousal (SES/SIS) - 24 questions
  - Preferences - 46 questions  
  - Boundaries & Context - 10 questions
  - Role & Logistics - 6 questions
  - Ipsative (Current Tilt) - 6 questions
- **Chapter-by-chapter navigation** with progress tracking
- **Session persistence** using LocalStorage (answers saved automatically)
- **Name collection** before survey starts
- **Validation** to ensure all required questions are answered

### 2. **Question Types**
- **Likert-7 Scale**: 1-7 rating with visual slider
- **YMN (Yes/Maybe/No)**: Three-option choice for preferences
- **Choose2 (A/B)**: Binary choice for ipsative questions
- **Boundary**: Optional safety/boundary questions

### 3. **Scoring Engine**
Implements the complete IntimacAI v0.2.3 scoring algorithm:

#### **Trait Calculation**
- 18 psychological traits calculated from weighted question responses
- Includes: SE, SIS_P, SIS_C, NOVELTY, RISK, SENSUAL, ROMANTIC, CONTROL_PREF, POWER_TOP, POWER_BOTTOM, VOYEUR, EXHIB, GROUP, ENM_OPEN, AFTERCARE, COMM, BODY_CONF, PERF_ANXI

#### **Dial Calculation**  
Four key dimensions derived from trait combinations:
- **Adventure**: Novelty + Risk appetite
- **Connection**: Romantic + Sensual + Aftercare needs
- **Intensity**: Power dynamics + Edge play interest
- **Confidence**: Body confidence - Performance anxiety

#### **Archetype Assignment**
- 12 archetypes based on dial scores
- Top 3 archetypes displayed in order
- Includes: Explorer, Sensualist, Romantic, Adventurer, Hedonist, Connector, Devotee, Dominant, Switch, Submissive, Steady, Cautious

### 4. **Compatibility Matching**
Advanced matching algorithm with:
- **Category-based alignment** across 12 intimacy categories
- **Power complement calculation** (top/bottom compatibility)
- **Boundary gates** (hard limits must be respected)
- **Overall compatibility score** (0-100%)
- **Detailed breakdown** by category

### 5. **Admin Panel**
Password-protected admin interface (password: `1111`):
- **View all submissions** in a sortable table
- **Set baseline** for compatibility comparison
- **Export data** as CSV or JSON
- **Version history** tracking (v0.2.3 current)

### 6. **Data Management**
- **LocalStorage persistence** for all submissions
- **Unique submission IDs** (timestamp-based)
- **Session recovery** (resume incomplete surveys)
- **Export capabilities** for research/analysis

---

## Technical Architecture

### **Frontend Framework**
- **React 18** with functional components and hooks
- **React Router** for navigation
- **Vite** for fast development and optimized builds

### **UI Components**
- **shadcn/ui** component library
- **Tailwind CSS** for styling
- **Lucide React** icons
- Fully responsive design (mobile, tablet, desktop)

### **Data Structure**
```javascript
{
  id: "timestamp-uuid",
  name: "User Name",
  createdAt: "ISO timestamp",
  answers: {
    A1: 5,
    B1: "Y",
    IA1: "A",
    // ... all 92 questions
  },
  derived: {
    traits: { SE: 65.2, NOVELTY: 72.1, ... },
    dials: { Adventure: 68.5, Connection: 75.2, ... },
    archetypes: [
      { id: "explorer", name: "Explorer", score: 85.3, desc: "..." },
      // ... top 3
    ],
    boundaryFlags: { HARD_LIMITS: [], SOFT_LIMITS: [] }
  }
}
```

### **File Structure**
```
attuned-survey/
├── src/
│   ├── data/
│   │   ├── schema.json          # Survey schema v0.2.3
│   │   ├── questions.csv        # Question bank
│   │   └── AttunedLogo.png      # Brand logo
│   ├── lib/
│   │   ├── scoring/
│   │   │   ├── traitCalculator.js
│   │   │   ├── dialCalculator.js
│   │   │   └── archetypeCalculator.js
│   │   ├── matching/
│   │   │   ├── categoryMap.js
│   │   │   └── overlapHelper.js
│   │   ├── storage/
│   │   │   └── submissionStore.js
│   │   └── surveyData.js
│   ├── pages/
│   │   ├── Landing.jsx          # Home page
│   │   ├── Survey.jsx           # Survey flow
│   │   ├── Result.jsx           # Results display
│   │   ├── Admin.jsx            # Admin panel
│   │   └── Privacy.jsx          # Privacy policy
│   ├── App.jsx                  # Main app with routing
│   └── main.jsx                 # Entry point
├── dist/                        # Production build
└── package.json
```

---

## How to Use the Deployed Website

### **For Survey Takers**

1. **Visit the homepage**
   - Read the welcome message and instructions
   - Click "Start Your Survey"

2. **Enter your name**
   - Provide your name for personalized results
   - Click "Continue"

3. **Complete the survey**
   - Answer questions honestly (no wrong answers)
   - Use "Next" to move between chapters
   - Your progress is saved automatically
   - You can close and resume later

4. **View your results**
   - See your archetype(s)
   - Review your four dimension scores
   - If a baseline is set, see compatibility match

5. **Edit if needed**
   - Click "Edit Answers" to modify responses
   - Results update automatically

### **For Administrators**

1. **Access admin panel**
   - Navigate to `/admin`
   - Enter password: `1111`

2. **View responses**
   - See all submissions in table format
   - Review dials and archetypes
   - Set baseline for matching

3. **Export data**
   - Download CSV for spreadsheet analysis
   - Download JSON for programmatic use

4. **Manage baselines**
   - Click "Set" next to any submission
   - All future submissions will show compatibility

---

## Testing Checklist

✅ Landing page displays correctly  
✅ Survey navigation works (Previous/Next)  
✅ Questions display with proper UI  
✅ Progress bar updates correctly  
✅ Session persistence (refresh recovery)  
✅ Scoring calculations execute  
✅ Results page shows archetypes and dials  
✅ Admin login works (password: 1111)  
✅ Data export functions (CSV/JSON)  
✅ Responsive design on mobile/tablet  
✅ Accessibility (keyboard navigation, ARIA labels)

---

## Browser Compatibility

- **Chrome/Edge**: ✅ Fully supported
- **Firefox**: ✅ Fully supported  
- **Safari**: ✅ Fully supported
- **Mobile browsers**: ✅ Responsive design

---

## Data Privacy & Security

- **Local storage only**: All data stored in browser LocalStorage
- **No server-side storage**: Privacy-first approach
- **No tracking**: No analytics or third-party scripts
- **Export control**: Users/admins control data export
- **Password-protected admin**: Simple password gate for admin features

---

## Future Enhancements (Not Implemented)

The following were specified but marked as future work:
- **Lite version**: Shorter 30-question survey
- **Version rollback**: Restore previous schema versions
- **Advanced analytics**: Aggregate statistics dashboard
- **Multi-language support**: Internationalization
- **Email results**: Send results via email
- **PDF export**: Download results as PDF

---

## Support & Documentation

### **Original Specifications**
- Survey Schema: `intimacai_survey_schema_v0.2.3.json`
- Question Bank: `intimacai_question_bank_v0.2.3.csv`
- Requirements: `AttunedSurveyPrototypeRequirements–v0.2.3.docx`
- README: `README_IntimacAI_EndToEnd_v0.2.3.md`

### **Technical References**
- Overlap Helper: `intimacai_overlap_helper_v0.2.3.ts`
- Category Map: `intimacai_overlap_map_v0.2.2.ts`

---

## Deployment URL

Once you click **Publish**, you'll receive a permanent public URL in the format:

```
https://[unique-id].manus.app
```

This URL will be:
- ✅ **Permanent** (won't expire)
- ✅ **HTTPS-secured**
- ✅ **Globally accessible**
- ✅ **Fast CDN delivery**

---

## Credits

**Built with**: [Manus](https://manus.im)  
**Version**: 0.2.3  
**Date**: October 2025

---

## Quick Start Commands

If you need to modify the application locally:

```bash
# Navigate to project
cd /home/ubuntu/attuned-survey

# Install dependencies (already done)
pnpm install

# Start development server
pnpm run dev

# Build for production
pnpm run build

# Preview production build
pnpm run preview
```

---

**Ready to publish!** Click the Publish button in your interface to deploy the website.

