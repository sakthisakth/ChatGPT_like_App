
# ChatGPT-like Chat App (Python + FastAPI + MongoDB + Vercel)

A minimal ChatGPT-style chat UI with a Python FastAPI backend that stores all messages in MongoDB.
It runs locally with Uvicorn and deploys to Vercel (free tier).

## Features
- Simple, clean ChatGPT-like frontend (HTML/CSS/JS).
- Python FastAPI backend with `/api/chat`, `/api/history`, `/api/health`.
- Stores **every** message (user + assistant) in MongoDB (Atlas or self-hosted).
- Session-based chats using a generated `session_id` stored in browser `localStorage`.
- Works locally and on Vercel.

---

## 1) Prerequisites
- **Python 3.11+**
- **MongoDB Atlas** (free cluster) or your own MongoDB
- (Optional) **Vercel CLI** if you want to deploy from terminal: `npm i -g vercel`

---

## 2) MongoDB Setup
1. Create a free MongoDB Atlas cluster.
2. Create a database user and allow your IP to access.
3. Copy the **connection string** like:
   `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
4. Set the database name and collection (defaults used):
   - DB: `chatdb`
   - Collection: `messages`

---

## 3) Local Development

1. Clone this repository and enter the folder.
2. Create `.env` with your Mongo URI:
   ```env
   MONGODB_URI="your mongodb+srv://... string here"
   MONGODB_DB="chatdb"
   MONGODB_COLLECTION="messages"
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the API locally (from repo root):
   ```bash
   uvicorn api.chat:app --reload
   ```
5. Open `public/index.html` using a simple server, or just open it from disk.
   - If you open from disk, change `API_BASE` at the top of `public/index.html` to `http://127.0.0.1:8000`.
   - Alternatively, serve `public` via a static server (e.g. `python -m http.server`) and keep `API_BASE` as empty string if you reverse-proxy.
6. Chat! Messages will be saved to MongoDB. Click **New Chat** to start a new `session_id`.

---

## 4) Deploy to Vercel (Free)

**Option A: One-click-ish via Vercel UI**
1. Push this project to a **GitHub** repository.
2. Go to **vercel.com > New Project > Import GitHub Repo**.
3. Framework Preset: **Other**.
4. Root directory: the repo root.
5. Add **Environment Variables**:
   - `MONGODB_URI` = your MongoDB connection string
   - `MONGODB_DB` = `chatdb`
   - `MONGODB_COLLECTION` = `messages`
6. Deploy. Vercel will detect `api/chat.py` with the Python runtime.
7. Visit your Vercel URL. The frontend will be served from `public/index.html`.
   - The API is available at `/api/chat`, `/api/history`.
   - If you need CORS, it's already enabled.

**Option B: Vercel CLI**
```bash
vercel login
vercel
# On first deploy, follow prompts (project name, root directory).
# Then set envs:
vercel env add MONGODB_URI
vercel env add MONGODB_DB
vercel env add MONGODB_COLLECTION
# Redeploy to apply envs:
vercel --prod
```

---

## 5) Notes & Customization
- The current "assistant" is a **dummy** that echoes/acknowledges messages. Replace `_assistant_reply()` in `api/chat.py` with a real LLM call if permitted.
- The DB schema is schemaless. Each message doc looks like:
  ```json
  {
    "session_id": "uuid",
    "role": "user" | "assistant",
    "text": "message",
    "created_at": "2025-08-20T12:34:56Z",
    "username": "user"
  }
  ```
- You can add indexes in MongoDB for performance:
  - `messages.createIndex({ session_id: 1, created_at: 1 })`

---

## 6) Troubleshooting
- **ImportError**: Ensure Python 3.11+ and `pip install -r requirements.txt`.
- **CORS issues**: When testing locally, set `API_BASE` in `index.html` to your API origin (e.g., `http://127.0.0.1:8000`).
- **MongoDB connection errors**: Confirm IP allowlist, user/password, and that `MONGODB_URI` is set in `.env` (locally) or Vercel Env Vars (cloud).
- **404 on /api/chat** on Vercel: Make sure `vercel.json` exists in repo root and you deployed the root (not a subdir).

---

## 7) Local "All-in-one" preview (optional)
If you want to serve the static frontend via any static server while the API runs with Uvicorn:
```bash
# Terminal A (API)
uvicorn api.chat:app --reload

# Terminal B (Static files from /public)
cd public
python -m http.server 5500
# Then open http://127.0.0.1:5500/ and set API_BASE in index.html to http://127.0.0.1:8000
```

---

## License
MIT
