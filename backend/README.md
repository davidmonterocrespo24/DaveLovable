# GitLab Clone - Modern Frontend Implementation

A modern, responsive GitLab clone built with React, TypeScript, and Tailwind CSS. This is a frontend-only implementation with mock data to demonstrate a complete GitLab-like interface.

## Features

### 🎨 **Modern UI Components**
- **Sidebar Navigation**: Collapsible sidebar with project groups and menu items
- **Header**: Search bar, notifications, user profile, and quick stats
- **Project Cards**: Display project details with visibility badges, star/fork counts
- **Merge Request Cards**: Show MR status, approvals, branch information
- **Issue Cards**: Issue tracking with labels, assignees, and milestones
- **Dashboard**: Comprehensive overview with stats and recent activity

### 📊 **Dashboard Features**
- Real-time statistics (projects, MRs, issues, pipelines)
- Recent activity feed
- Pipeline status monitoring
- Quick action buttons
- Responsive grid layout

### 🛠️ **Technical Implementation**
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first styling
- **Mock Services**: Complete mock API service with realistic data
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Component Architecture**: Modular, reusable components

## Project Structure

```
src/
├── components/
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── Header.tsx         # Top header with search
│   ├── ProjectCard.tsx    # Project display card
│   ├── MergeRequestCard.tsx # MR display card
│   └── IssueCard.tsx      # Issue display card
├── services/
│   └── mockGitLabService.ts # Mock API service
├── utils/
│   └── helpers.ts         # Utility functions
├── App.tsx               # Main application
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## Mock Data

The application includes comprehensive mock data for:
- **Projects**: 5 sample projects with different visibility levels
- **Users**: 3 team members with profiles
- **Merge Requests**: 3 MRs with different states (open, merged, closed)
- **Issues**: 3 issues with labels and assignees
- **Pipelines**: 3 pipeline runs with different statuses

## Getting Started

### Prerequisites
- Node.js 18+ and npm/yarn/pnpm

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production
```bash
npm run build
```

## Key Components

### 1. **Sidebar**
- Project groups with counts
- Main navigation menu
- User profile section
- System status indicator

### 2. **Header**
- Global search functionality
- Notification bell with badge
- Quick "New" action button
- User profile dropdown

### 3. **Project Cards**
- Project name with namespace
- Visibility badges (Public/Private/Internal)
- Star and fork counts
- Last activity timestamp
- Archive status indicator

### 4. **Merge Request Cards**
- MR number and title
- State indicators (Open/Merged/Closed)
- Upvote/downvote counts
- Author and assignee avatars
- Branch information

### 5. **Dashboard**
- Statistics cards with icons
- Recent activity timeline
- Pipeline status monitor
- Quick action buttons

## Styling

The application uses **Tailwind CSS** with:
- Custom color palette matching GitLab's aesthetic
- Responsive breakpoints
- Hover and focus states
- Smooth transitions
- Gradient backgrounds

## Utilities

The `helpers.ts` file provides utility functions for:
- Date formatting (relative time)
- Text truncation
- Pipeline status colors
- File size formatting
- Label color generation
- Debounce for search inputs

## Future Enhancements

Potential improvements that could be added:
1. **Real API Integration**: Connect to actual GitLab API
2. **Authentication**: User login and session management
3. **State Management**: Add Zustand or Redux for global state
4. **Real-time Updates**: WebSocket connections for live updates
5. **Advanced Search**: Full-text search across all entities
6. **Dark Mode**: Toggle between light and dark themes
7. **Accessibility**: Improve keyboard navigation and screen reader support

## Technologies Used

- **React 18**: Frontend library
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling framework
- **Lucide React**: Icon library
- **Vite**: Build tool and dev server
- **Mock Service**: Simulated API responses

## License

This project is for demonstration purposes only. GitLab is a trademark of GitLab Inc.

---

**Note**: This is a frontend-only implementation. All data is mocked for demonstration purposes. In a real application, you would connect to the GitLab API or your own backend service.