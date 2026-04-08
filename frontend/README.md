# OpenPilot-UI

A dashboard for managing and annotating autonomous vehicle route data collected by [OpenPilot](https://github.com/commaai/openpilot). The UI provides a pipeline view from raw recorded routes through segmentation, annotation (via CVAT), and review giving you a single place to track where everything stands.

**Author:** Thomas Petersen

---

## What it does

Routes recorded by a comma device get processed through several stages before they're useful for training. This app surfaces that pipeline:

- Browse all routes with filtering by status, sorting, and a quick search
- Drill into a route to see its individual segments laid out in a grid
- Open any segment directly in CVAT to annotate or review it
- Configure your CVAT and PostgreSQL connections from the Settings page

The annotation statuses move through: `recorded → segmented → annotating → annotated → reviewed` (or `failed` at any point).

---

## Project structure

```
OpenPilot-UI/
├── frontend/
│   ├── public/
│   │   └── mock_images/        # Placeholder thumbnails for development
│   └── src/
│       ├── components/
│       │   └── TopBar.tsx      # Top navigation bar
│       ├── layouts/
│       │   └── AppLayout.tsx   # Shared page wrapper
│       ├── pages/
│       │   ├── RouteDashboard.tsx   # Route list with stats and filters
│       │   ├── RouteDetail.tsx      # Single route — segment grid and timeline
│       │   ├── SegmentViewer.tsx    # Single segment — CVAT link and annotation breakdown
│       │   └── Settings.tsx         # CVAT and PostgreSQL connection settings
│       ├── App.tsx             # Route definitions
│       ├── main.tsx            # Entry point
│       └── index.css           # Design tokens (colors, spacing, typography)
├── docker-compose.yml
└── README.md
```

### Pages and routes

| Path | Page | What it shows |
|---|---|---|
| `/routes` | Route Dashboard | All routes filterable, sortable, with a stats strip |
| `/routes/:routeId` | Route Detail | Segment grid, timeline, completion bar |
| `/routes/:routeId/segments/:segmentId` | Segment Viewer | Segment metadata, CVAT link, annotation breakdown |
| `/settings` | Settings | CVAT + PostgreSQL connection config |

---

## Tech stack

- **React 19** + **TypeScript**
- **React Router 7** for navigation
- **Vite** as the dev server and bundler
- **Tailwind CSS 4** for utility classes
- **CSS custom properties** for the design system all colors, spacing, and typography live in `index.css` as variables so the whole app can be re-themed from one file
- **Lucide React** for icons
- **Docker** for containerized development with hot reload

---

## Design system

Everything visual is driven by CSS variables defined in `src/index.css`. The main categories:

- **Backgrounds** — `--bg-primary`, `--bg-surface`, `--bg-elevated`, `--bg-inverse`
- **Text** — `--text-primary`, `--text-secondary`, `--text-muted`, `--text-on-inverse`
- **Status accents** — `--accent-go` (green), `--accent-caution` (amber), `--accent-alert` (red)
- **Status badge tints** — paired text and background colors for each status badge
- **Annotation class colors** — one color per object class (vehicle, pedestrian, cyclist, etc.)
- **Service accents** — `--accent-cvat` (purple), `--accent-postgres` (blue)

Typography uses **General Sans** for UI text and **Space Mono** for all IDs, timestamps, and data.

---

## Running locally

The app runs in Docker. From the project root:

```bash
docker compose watch
```

Frontend is served at **http://localhost:5173**

The `watch` command enables hot reload file changes in `src/` sync into the container automatically, no restart needed.

---

## Current state

The frontend is fully built out and working against mock data. The integration points reading real routes from PostgreSQL and constructing CVAT task links are defined but not yet wired to a backend. The Settings page is ready to accept and persist real connection config once that layer exists.

The mock data lives in the page files for now and will be replaced as the backend comes online.
