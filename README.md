## 🌐 Live Demo

> **Live App:** [ai-pptcon-frontend.vercel.app](https://ai-pptcon-frontend.vercel.app/)

# AI PPTCon

AI PPTCon is a full-stack web application for generating and converting PowerPoint presentations with AI. Users can create a new `.pptx` from a topic and prompt, convert an existing presentation into a new template, manage their profile, view dashboard statistics, track activity, and use an in-app chatbot/help flow.

## Features

- AI-powered PPT generation from a topic, optional description, slide count, layout preference, and uploaded/selected template.
- PPT template conversion that transfers content from one presentation into another template.
- AI refinement for converted presentations with smarter text placement and formatting.
- Template library APIs for listing, previewing, and downloading templates.
- User authentication with email/password, Google OAuth support on the frontend, JWT sessions, profile updates, preferences, and avatar uploads.
- Dashboard, activity, and analytics pages for tracking generated presentations and conversions.
- Chatbot and help/contact flows.
- MongoDB support with JSON-file fallback for local development.
- Image sourcing for generated slides through Unsplash, Pexels, Pollinations, and placeholder fallback.

## Tech Stack

### Frontend

- React 18
- Vite 6
- TypeScript
- Tailwind CSS
- Radix UI components
- React Router
- TanStack Query
- Axios
- Framer Motion
- Recharts

### Backend

- Python 3
- Flask
- Flask-CORS
- python-pptx
- MongoDB / PyMongo
- Google Gemini API
- JWT authentication
- bcrypt password hashing
- Pillow
- Gunicorn for deployment

## Project Structure

```text
.
├── backend/
│   ├── app.py                  # Main Flask API server
│   ├── database.py             # MongoDB connection and migration helpers
│   ├── requirements.txt        # Backend Python dependencies
│   ├── Procfile                # Gunicorn start command for deployment
│   ├── render-build.sh         # Render build script
│   ├── utils/
│   │   ├── ppt_processor.py    # PPT generation, conversion, refinement, image logic
│   │   └── layout_extractor.py # Template layout extraction
│   └── uploads/                # Uploaded/generated template and image assets
├── frontend/
│   ├── src/
│   │   ├── pages/              # App pages: Dashboard, Generate, Convert, Analytics, etc.
│   │   ├── components/         # Navbar, auth modal, profile modal, UI components
│   │   ├── contexts/           # Auth and theme providers
│   │   └── utils/axios.ts      # API client
│   ├── package.json
│   ├── vite.config.ts
│   └── vercel.json             # Vercel SPA routing config
├── Uploads/                    # Runtime upload folder used by backend
├── outputs/                    # Generated PPT output folder
├── templates/                  # Local PPT template folder
└── README.md
```

## Prerequisites

- Node.js 18 or newer
- npm
- Python 3.10 or newer
- MongoDB local server or MongoDB Atlas connection string
- Google Gemini API key

Optional image providers:

- Unsplash API key
- Pexels API key
- Pollinations can work without a key in the current code path

## Environment Variables

Create a `.env` file inside `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=pptcon_db

JWT_SECRET=replace_with_a_strong_secret

UNSPLASH_API_KEY=optional_unsplash_key
PEXELS_API_KEY=optional_pexels_key
POLLINATIONS_API_KEY=optional_pollinations_key

EMAIL_USER=optional_sender_email
EMAIL_PASS=optional_sender_app_password
EMAIL_RECEIVER=optional_receiver_email
```

Create a `.env` file inside `frontend/`:

```env
VITE_API_URL=http://localhost:5050
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

If `VITE_API_URL` is not set, the frontend defaults to `http://localhost:5050`.

## Local Setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The backend is expected to run on:

```text
http://localhost:5050
```

If MongoDB is not available, the app falls back to JSON files for user/chat/dashboard data where implemented.

### 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server is configured for:

```text
http://localhost:8080
```

## Useful Commands

### Frontend

```bash
npm run dev
npm run build
npm run typecheck
npm run test
npm run format.fix
```

### Backend

```bash
python app.py
python test_gemini.py
python test_gemini_models.py
python check_mongodb.py
python migrate_to_mongodb.py
```

## Main API Endpoints

### Authentication

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/google`
- `GET /api/auth/me`
- `PUT /api/auth/profile`
- `POST /api/auth/avatar`
- `GET /api/auth/avatar`
- `GET /api/auth/preferences`
- `PUT /api/auth/preferences`

### PPT Generation and Conversion

- `POST /get-layouts` - Extract layouts from an uploaded PPT template.
- `POST /upload` - Convert a content PPT into a selected template.
- `POST /refine` - Refine a converted PPT with improved layout/text placement.
- `POST /generate-ai-content` - Generate slide content using AI.
- `POST /generate-ppt-ai` - Generate an AI PPT.
- `POST /generate-ppt-ai-enhanced` - Generate an enhanced AI PPT with slide count and layout preferences.
- `GET /get-content/<filename>` - Download content files.
- `GET /get-image/<filename>` - Serve generated/fetched images.
- `GET /get-ppt/<filename>` - Download generated PPT files.

### Templates

- `GET /get-templates`
- `GET /api/templates`
- `GET /api/templates/popular`
- `GET /api/templates/<template_id>`
- `POST /api/templates/<template_id>/download`

### Dashboard and Analytics

- `GET /api/dashboard/stats`
- `POST /api/dashboard/activity`
- `DELETE /api/dashboard/activity/<activity_id>`
- `GET /api/dashboard/presentations`
- `POST /api/dashboard/presentation`
- `GET /api/analytics/overview`
- `GET /api/analytics/performance`
- `GET /api/analytics/usage`
- `GET /api/analytics/export`

### Chat and Support

- `GET /api/chat/history`
- `POST /api/chat/history`
- `DELETE /api/chat/history/<session_id>`
- `POST /chatbot`
- `POST /contact`
- `POST /feedback`

## How It Works

1. The user signs up or logs in from the React frontend.
2. The frontend stores the JWT token in `sessionStorage` and sends it through Axios request interceptors.
3. For AI generation, the user provides a topic, optional instructions, slide count, layout preference, and a template.
4. Flask receives the request, calls Gemini for structured slide content, fetches or generates relevant slide images, and uses `python-pptx` to create a downloadable `.pptx`.
5. For conversion, the backend reads both uploaded PPT files and maps content into the target template.
6. Dashboard and analytics endpoints record and return user-specific usage data.

## Deployment Notes

### Frontend on Vercel

The frontend includes `frontend/vercel.json`, which routes all paths to `index.html` for SPA routing.

Build command:

```bash
npm run build
```

Output directory:

```text
dist/spa
```

Set `VITE_API_URL` in Vercel to the deployed backend URL.

### Backend on Render or Similar Platforms

The backend includes:

- `backend/Procfile`
- `backend/render-build.sh`

Start command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2
```

Set all backend environment variables in the hosting provider dashboard.

## Troubleshooting

- **Gemini generation fails**: Check `GEMINI_API_KEY` and `GEMINI_MODEL` in `backend/.env`.
- **Frontend cannot reach backend**: Verify `VITE_API_URL` and confirm Flask is running on port `5050`.
- **MongoDB connection fails**: Start local MongoDB or set a valid Atlas `MONGODB_URI`. The backend logs connection errors on startup.
- **PPT download is empty or broken**: Confirm uploaded files are valid `.pptx` files and not corrupted.
- **Images are missing in generated slides**: Add `UNSPLASH_API_KEY` or `PEXELS_API_KEY`; otherwise the app attempts Pollinations and placeholder fallback.
- **Google login does not work**: Set `VITE_GOOGLE_CLIENT_ID` and configure the correct authorized origins in Google Cloud Console.

## Notes

- Runtime folders such as `Uploads/`, `outputs/`, `templates/`, and `backend/uploads/` are used to store generated or uploaded files.
- The root `requirements.txt` appears to contain encoding artifacts; use `backend/requirements.txt` for backend installation.
- Keep secrets out of Git. Use `.env` files locally and environment variables in production.
