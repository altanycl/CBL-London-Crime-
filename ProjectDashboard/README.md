# London Crime Dashboard

A NextJS dashboard application for visualizing London crime data, statistics, and forecasting.

## Features

- Interactive maps showing past burglaries and predicted hotspots
- Filtering by borough, ward, and LSOA levels
- Year and month selection via sliders
- Police resource allocation recommendations
- Prediction metrics and statistics
- Explainability reports and fairness checks
- Interactive popouts for detailed information

## Tech Stack

- NextJS 14
- TypeScript
- Tailwind CSS
- ShadCN UI Components
- SVG Placeholders (later to be replaced with React Leaflet for maps and Recharts for charts)

## Prerequisites

Before you begin, ensure you have the following installed:
- Node.js (v18 or later)
- npm (v9 or later)

## Getting Started

1. Clone this repository:
```bash
git clone https://github.com/yourusername/london-crime-dashboard.git
cd london-crime-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to see the dashboard.

## Fixing TypeScript Errors

If you encounter TypeScript errors related to missing d3 or geojson type definitions:

1. Run the install-types script to install all necessary type definitions:
```bash
npm run install-types
```

2. If TypeScript errors persist, they are handled in the build config with `typescript.ignoreBuildErrors` set to `true` in `next.config.js`.

## Interactive Popouts

The dashboard features interactive popouts for detailed information:

1. **Explainability Report** - Shows how the prediction model works, including:
   - Key features influencing predictions
   - Model architecture details
   - Feature engineering methodology
   
2. **Fairness Check** - Analyzes model fairness across demographics:
   - Fairness metrics (Equal Opportunity, Demographic Parity, etc.)
   - Demographic distribution analysis
   - Area-based fairness evaluations
   
3. **Duty Sheet** - Provides recommended patrol areas and schedules:
   - Area-specific patrol assignments
   - Priority levels and resource allocations
   - Interactive controls for viewing all areas
   - Print functionality

Popouts are implemented using ShadCN UI's Dialog component, providing a responsive and accessible interface for detailed information.

## Project Structure

- `/app` - Next.js app router files
- `/components` - React components
  - `/ui` - ShadCN UI components
- `/lib` - Utility functions
- `/public` - Static assets including SVG placeholders
- `/types` - TypeScript declaration files

## Future Implementation

In a production environment, the placeholder SVGs would be replaced with:
- Real-time data from London crime APIs
- Interactive maps using React Leaflet
- Dynamic charts with Recharts
- Authentication for secure access

## Data Sources

This dashboard is designed to work with London crime data from the following sources:
- Metropolitan Police crime data
- London Datastore

## Troubleshooting

If you encounter the "Event handlers cannot be passed to Client Component props" error, ensure that all components using interactivity (like `FilterPanel`) have the "use client" directive at the top of the file.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 