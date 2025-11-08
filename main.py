# main.py
from fastapi import FastAPI, Request, Form, Response, HTTPException, Depends, status
from fastapi import FastAPI, BackgroundTasks
from fastapi import File, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import secrets
import httpx # For making HTTP requests to Google OAuth
from typing import Optional, List, Dict, Any
import sqlite3
import dotenv
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

# Local imports
from database import get_db_connection, init_db # init_db is now more comprehensive
from security import hash_password, verify_password, sanitize_input, get_password_strength, create_reset_token
from email_utils import send_password_reset_email

# Initialize database
init_db()

dotenv.load_dotenv()

app = FastAPI()

# Configuration for Session Middleware (required for sessions and OAuth)
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_hex(32))
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

AVATAR_DIR = Path("static/assets/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

USER_DATA_DIR = Path("users") # Root user data directory
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Google OAuth Configuration ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback") 

if GOOGLE_CLIENT_ID == "YOUR_GOOGLE_CLIENT_ID" or GOOGLE_CLIENT_SECRET == "YOUR_GOOGLE_CLIENT_SECRET":
    print("WARNING: Google OAuth credentials are not set. OAuth will not function.")
    print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")


# --- Helper Functions ---
def get_current_user_id(request: Request) -> Optional[int]:
    return request.session.get("user_id")

def get_current_username(request: Request) -> Optional[str]:
    user_id = get_current_user_id(request)
    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return user["username"] if user else None
    return None

def get_current_user_data(request: Request) -> Optional[dict]:
    user_id = request.session.get("user_id")
    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute("SELECT id, username, email, avatar_url FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if user:
            avatar_url_db = user["avatar_url"] if "avatar_url" in user.keys() else None
            if avatar_url_db:
                if avatar_url_db.startswith("/static/assets/avatars/"):
                    avatar_file = AVATAR_DIR / Path(avatar_url_db).name
                    avatar_url = avatar_url_db if avatar_file.exists() else "/static/assets/images/default-avatar.png"
                else:
                    avatar_url = avatar_url_db
            else:
                avatar_path = AVATAR_DIR / f"{user['username']}.png"
                avatar_url = f"/static/assets/avatars/{user['username']}.png" if avatar_path.exists() else "/static/assets/images/default-avatar.png"
            return {"id": user["id"], "username": user["username"], "email": user["email"], "avatar_url": avatar_url}
    return None

def is_admin_user(request: Request) -> bool:
    user_data = get_current_user_data(request)
    return user_data and user_data["username"] == "TieSinger"

# --- Middleware ---
@app.middleware("http")
async def create_user_data_dir_middleware(request: Request, call_next):
    response = await call_next(request)
    user_id = request.session.get("user_id")
    if user_id and not request.session.get("user_dir_checked"):
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if user:
            user_username = user["username"]
            user_specific_dir = USER_DATA_DIR / user_username
            user_specific_dir.mkdir(parents=True, exist_ok=True)
            request.session["user_dir_checked"] = True
    return response

# --- Standard Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user_data = get_current_user_data(request)
    return templates.TemplateResponse("index.html", {"request": request, "name": "TieSinger", "user_data": user_data})

# --- Authentication Routes ---
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    user_data = get_current_user_data(request)
    success_message = request.session.pop("success", None)
    return templates.TemplateResponse("login.html", {"request": request, "user_data": user_data, "success": success_message})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id, username, hashed_password FROM users WHERE username = ?", (sanitize_input(username),)).fetchone()
    conn.close()

    if user and verify_password(password, user["hashed_password"]):
        request.session["user_id"] = user["id"]
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    else:
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password", "user_data": user_data})

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    user_data = get_current_user_data(request)
    return templates.TemplateResponse("register.html", {"request": request, "user_data": user_data})

@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords do not match.", "user_data": user_data})

    strength = get_password_strength(password)
    if strength["score"] < 60:
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("register.html", {"request": request, "error": "Password is too weak. " + " ".join(strength["feedback"]), "user_data": user_data})

    hashed_password = hash_password(password)
    sanitized_username = sanitize_input(username)
    sanitized_email = sanitize_input(email)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        default_avatar = "/static/assets/images/default-avatar.png"
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password, avatar_url) VALUES (?, ?, ?, ?)",
            (sanitized_username, sanitized_email, hashed_password, default_avatar)
        )
        conn.commit()
        user = cursor.execute("SELECT id FROM users WHERE username = ?", (sanitized_username,)).fetchone()
        request.session["user_id"] = user["id"]
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    except sqlite3.IntegrityError:
        conn.rollback()
        error_msg = "Username or Email already registered."
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("register.html", {"request": request, "error": error_msg, "user_data": user_data})
    finally:
        conn.close()

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

# --- NEW: Password Reset Routes ---

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_get(request: Request):
    user_data = get_current_user_data(request) # For header context
    return templates.TemplateResponse("forgot_password.html", {"request": request, "user_data": user_data})

@app.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_post(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...)
):
    user_data = get_current_user_data(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id, email, username FROM users WHERE email = ?", (sanitize_input(email),)).fetchone()

    if not user:
        conn.close()
        return templates.TemplateResponse("forgot_password.html", {"request": request, "user_data": user_data, "success": "If an account with that email exists, reset instructions will be sent."})

    token, expires_at = create_reset_token()
    
    try:
        cursor.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user["id"], token, expires_at)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return templates.TemplateResponse("forgot_password.html", {"request": request, "user_data": user_data, "error": f"An error occurred: {e}"})
    finally:
        conn.close()
    
    reset_link = request.url_for('reset_password_get', token=token)
    
    background_tasks.add_task(
        send_password_reset_email,
        to_email=user["email"],
        username=user["username"],
        reset_link=str(reset_link)
    )

    return templates.TemplateResponse("forgot_password.html", {"request": request, "user_data": user_data, "success": "If an account with that email exists, reset instructions have been sent." })


@app.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_get(request: Request, token: str):
    user_data = get_current_user_data(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    token_data = cursor.execute(
        "SELECT user_id, expires_at FROM password_reset_tokens WHERE token = ? AND expires_at > ?",
        (token, datetime.now())
    ).fetchone()
    
    conn.close()

    if not token_data:
        return templates.TemplateResponse("reset_password.html", {"request": request, "user_data": user_data, "error": "This reset link is invalid or has expired.", "invalid_token": True})
    
    return templates.TemplateResponse("reset_password.html", {"request": request, "user_data": user_data, "token": token})

@app.post("/reset-password", response_class=HTMLResponse)
async def reset_password_post(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    user_data = get_current_user_data(request)
    
    if new_password != confirm_password:
        return templates.TemplateResponse("reset_password.html", {"request": request, "user_data": user_data, "token": token, "error": "Passwords do not match."})

    strength = get_password_strength(new_password)
    if strength["score"] < 60:
        return templates.TemplateResponse("reset_password.html", {"request": request, "user_data": user_data, "token": token, "error": "Password is too weak. " + " ".join(strength["feedback"])})

    conn = get_db_connection()
    cursor = conn.cursor()
    
    token_data = cursor.execute(
        "SELECT id, user_id, expires_at FROM password_reset_tokens WHERE token = ? AND expires_at > ?",
        (token, datetime.now())
    ).fetchone()

    if not token_data:
        conn.close()
        return templates.TemplateResponse("reset_password.html", {"request": request, "user_data": user_data, "error": "This reset link is invalid or has expired.", "invalid_token": True})

    try:
        new_hashed_password = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET hashed_password = ? WHERE id = ?",
            (new_hashed_password, token_data["user_id"])
        )
        cursor.execute("DELETE FROM password_reset_tokens WHERE id = ?", (token_data["id"],))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return templates.TemplateResponse("reset_password.html", {"request": request, "user_data": user_data, "token": token, "error": f"An error occurred: {e}"})
    finally:
        conn.close()

    request.session["success"] = "Password reset successfully. Please log in with your new password."
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# --- Google OAuth Routes ---
@app.get("/auth/google")
async def google_auth(request: Request):
    scope = "openid profile email"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope={scope}"
    )
    return RedirectResponse(auth_url)

@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str):
    async with httpx.AsyncClient() as client:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = await client.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json["access_token"]

        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        userinfo_response = await client.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

    user_email = userinfo.get("email")
    user_google_id = userinfo.get("sub")

    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute("SELECT id, username, oauth_provider, oauth_id FROM users WHERE email = ? OR (oauth_provider = 'google' AND oauth_id = ?)", (user_email, user_google_id)).fetchone()

    if user:
        if user["oauth_provider"] != "google" or user["oauth_id"] != user_google_id:
            cursor.execute("UPDATE users SET oauth_provider = 'google', oauth_id = ? WHERE id = ?", (user_google_id, user["id"]))
            conn.commit()
        request.session["user_id"] = user["id"]
        conn.close()
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    else:
        request.session["oauth_email"] = user_email
        request.session["oauth_id"] = user_google_id
        request.session["oauth_provider"] = "google"
        conn.close()
        return RedirectResponse(url="/oauth-username", status_code=status.HTTP_302_FOUND)

@app.get("/oauth-username", response_class=HTMLResponse)
async def oauth_username_prompt(request: Request):
    oauth_email = request.session.get("oauth_email")
    if not oauth_email:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    user_data = get_current_user_data(request)
    return templates.TemplateResponse("username_prompt.html", {"request": request, "email": oauth_email, "user_data": user_data})

@app.post("/oauth-username", response_class=HTMLResponse)
async def oauth_username_submit(request: Request, username: str = Form(...)):
    oauth_email = request.session.get("oauth_email")
    oauth_id = request.session.get("oauth_id")
    oauth_provider = request.session.get("oauth_provider")

    if not (oauth_email and oauth_id and oauth_provider):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    sanitized_username = sanitize_input(username)
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_user = cursor.execute("SELECT id FROM users WHERE username = ?", (sanitized_username,)).fetchone()
    if existing_user:
        conn.close()
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("username_prompt.html", {"request": request, "email": oauth_email, "error": "Username already taken.", "user_data": user_data})

    try:
        placeholder_hashed_password = hash_password(secrets.token_urlsafe(16))
        default_avatar = "/static/assets/images/default-avatar.png"
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password, oauth_provider, oauth_id, avatar_url) VALUES (?, ?, ?, ?, ?, ?)",
            (sanitized_username, oauth_email, placeholder_hashed_password, oauth_provider, oauth_id, default_avatar)
        )
        conn.commit()
        new_user = cursor.execute("SELECT id FROM users WHERE username = ?", (sanitized_username,)).fetchone()
        request.session["user_id"] = new_user["id"]

        request.session.pop("oauth_email", None)
        request.session.pop("oauth_id", None)
        request.session.pop("oauth_provider", None)

        conn.close()
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("username_prompt.html", {"request": request, "email": oauth_email, "error": "Registration failed. Please try again.", "user_data": user_data})
    finally:
        conn.close()

# --- Project Routes ---
@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    user_data = get_current_user_data(request)
    return templates.TemplateResponse("projects.html", {"request": request, "user_data": user_data, "is_admin": is_admin_user(request)})

@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail_page(request: Request, project_id: int):
    user_data = get_current_user_data(request)
    conn = get_db_connection()
    cursor = conn.cursor()

    project = cursor.execute(
        "SELECT p.id, p.title, p.date_created, p.description, p.type, p.image_url, u.username as author_username "
        "FROM projects p JOIN users u ON p.author_id = u.id WHERE p.id = ?",
        (project_id,)
    ).fetchone()

    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    comments_db = cursor.execute(
        "SELECT pc.id, pc.comment_text, pc.created_at, pc.parent_id, u.username, pc.user_id as author_id, "
        "u.avatar_url as author_avatar_url "
        "FROM project_comments pc JOIN users u ON pc.user_id = u.id "
        "WHERE pc.project_id = ? ORDER BY pc.created_at ASC",
        (project_id,)
    ).fetchall()

    comments_by_id: Dict[int, Dict[str, Any]] = {}
    comments_list: List[Dict[str, Any]] = []

    for c in comments_db:
        comment_dict = dict(c)
        author_avatar = comment_dict["author_avatar_url"]
        if not author_avatar:
             author_avatar = "/static/assets/images/default-avatar.png"
        elif author_avatar.startswith("/static/assets/avatars/"):
            avatar_file = AVATAR_DIR / Path(author_avatar).name
            if not avatar_file.exists():
                author_avatar = "/static/assets/images/default-avatar.png"
        
        comment_dict["author_avatar"] = author_avatar
        comment_dict["author"] = comment_dict["username"]
        comment_dict["date"] = comment_dict["created_at"]
        comment_dict["text"] = comment_dict["comment_text"]
        comment_dict["children"] = []
        comments_by_id[comment_dict["id"]] = comment_dict

    for comment_id, comment_data in comments_by_id.items():
        parent_id = comment_data.get("parent_id")
        if parent_id and parent_id in comments_by_id:
            comments_by_id[parent_id]["children"].append(comment_data)
        elif not parent_id:
            comments_list.append(comment_data)

    reactions_db = cursor.execute(
        "SELECT reaction_type, COUNT(*) as count FROM project_reactions WHERE project_id = ? GROUP BY reaction_type",
        (project_id,)
    ).fetchall()

    reactions_counts = {"like": 0, "love": 0, "wow": 0}
    for r in reactions_db:
        reactions_counts[r["reaction_type"]] = r["count"]

    user_reaction = None
    if user_data:
        user_reaction_db = cursor.execute(
            "SELECT reaction_type FROM project_reactions WHERE project_id = ? AND user_id = ?",
            (project_id, user_data["id"])
        ).fetchone()
        if user_reaction_db:
            user_reaction = user_reaction_db["reaction_type"]

    conn.close()

    project_dict = {
        "id": project["id"],
        "title": project["title"],
        "date": project["date_created"],
        "description": project["description"],
        "type": project["type"],
        "image_url": project["image_url"],
        "author_username": project["author_username"],
        "comments": comments_list,
        "reactions": reactions_counts,
        "user_reaction": user_reaction
    }

    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "user_data": user_data,
        "project": project_dict,
        "is_admin": is_admin_user(request)
    })

# --- API Routes ---
@app.get("/api/projects", response_class=JSONResponse)
async def get_all_projects(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    projects_db = cursor.execute("SELECT id, title, date_created, short_description, type, image_url, author_id FROM projects ORDER BY date_created DESC").fetchall()
    conn.close()

    projects_list = []
    for p in projects_db:
        projects_list.append({
            "id": p["id"],
            "title": p["title"],
            "date": p["date_created"],
            "short_description": p["short_description"],
            "type": p["type"],
            "image_url": p["image_url"],
            "author_id": p["author_id"]
        })
    return JSONResponse(content=projects_list)

@app.post("/api/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    short_description: str = Form(...),
    type: str = Form(...),
    image_url: Optional[str] = Form(None),
    is_admin: bool = Depends(is_admin_user)
):
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not logged in")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO projects (title, date_created, description, short_description, type, image_url, author_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sanitize_input(title), date.today().isoformat(), description, sanitize_input(short_description), sanitize_input(type), image_url, user_id)
        )
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        return JSONResponse(content={"message": "Project created successfully", "id": project_id})
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create project: {e}")

@app.put("/api/projects/{project_id}")
async def update_project(
    request: Request,
    project_id: int,
    title: str = Form(...),
    description: str = Form(...),
    short_description: str = Form(...),
    type: str = Form(...),
    image_url: Optional[str] = Form(None),
    is_admin: bool = Depends(is_admin_user)
):
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE projects SET title = ?, description = ?, short_description = ?, type = ?, image_url = ? WHERE id = ?",
            (sanitize_input(title), description, sanitize_input(short_description), sanitize_input(type), image_url, project_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        conn.close()
        return JSONResponse(content={"message": "Project updated successfully"})
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update project: {e}")

@app.delete("/api/projects/{project_id}")
async def delete_project_api(
    request: Request,
    project_id: int,
    is_admin: bool = Depends(is_admin_user)
):
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM project_comments WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM project_reactions WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if cursor.fetchone():
             raise HTTPException(status_code=500, detail="Failed to delete project, check constraints.")
        conn.close()
        return JSONResponse(content={"message": "Project deleted successfully"})
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete project: {e}")

@app.post("/api/project/{project_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_project_comment(
    request: Request,
    project_id: int,
    comment_text: str = Form(...),
    parent_id: Optional[int] = Form(None)
):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not logged in")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO project_comments (project_id, user_id, comment_text, parent_id) VALUES (?, ?, ?, ?)",
            (project_id, user_id, comment_text, parent_id)
        )
        conn.commit()
        comment_id = cursor.lastrowid
        conn.close()
        return JSONResponse(content={"message": "Comment added successfully", "id": comment_id})
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add comment: {e}")

@app.put("/api/comments/{comment_id}")
async def edit_project_comment(
    request: Request,
    comment_id: int,
    comment_text: str = Form(...)
):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not logged in")
    conn = get_db_connection()
    cursor = conn.cursor()
    comment = cursor.execute("SELECT user_id FROM project_comments WHERE id = ?", (comment_id,)).fetchone()
    if not comment:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment["user_id"] != user_id:
        conn.close()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to edit this comment")
    try:
        cursor.execute(
            "UPDATE project_comments SET comment_text = ?, updated_at = ? WHERE id = ?",
            (comment_text, datetime.now().isoformat(), comment_id)
        )
        conn.commit()
        conn.close()
        return JSONResponse(content={"message": "Comment updated successfully"})
    except sqlite3.OperationalError:
        try:
            conn.rollback()
            cursor.execute(
                "UPDATE project_comments SET comment_text = ? WHERE id = ?",
                (comment_text, comment_id)
            )
            conn.commit()
            conn.close()
            return JSONResponse(content={"message": "Comment updated successfully"})
        except Exception as e:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update comment: {e}")
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update comment: {e}")

@app.delete("/api/comments/{comment_id}")
async def delete_project_comment(
    request: Request,
    comment_id: int
):
    user_id = get_current_user_id(request)
    is_admin = is_admin_user(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not logged in")
    conn = get_db_connection()
    cursor = conn.cursor()
    comment = cursor.execute("SELECT user_id FROM project_comments WHERE id = ?", (comment_id,)).fetchone()
    if not comment:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment["user_id"] != user_id and not is_admin:
        conn.close()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this comment")
    try:
        cursor.execute("DELETE FROM project_comments WHERE id = ?", (comment_id,))
        conn.commit()
        conn.close()
        return JSONResponse(content={"message": "Comment deleted successfully"})
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete comment: {e}")

@app.post("/api/project/{project_id}/reactions")
async def toggle_project_reaction(
    request: Request,
    project_id: int,
    reaction_type: str = Form(...)
):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not logged in")
    valid_reactions = ["like", "love", "wow"]
    if reaction_type not in valid_reactions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction type")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        existing_reaction = cursor.execute(
            "SELECT id, reaction_type FROM project_reactions WHERE project_id = ? AND user_id = ?",
            (project_id, user_id)
        ).fetchone()
        if existing_reaction:
            if existing_reaction["reaction_type"] == reaction_type:
                cursor.execute(
                    "DELETE FROM project_reactions WHERE id = ?",
                    (existing_reaction["id"],)
                )
                action = "removed"
            else:
                cursor.execute(
                    "UPDATE project_reactions SET reaction_type = ? WHERE id = ?",
                    (reaction_type, existing_reaction["id"])
                )
                action = "changed"
        else:
            cursor.execute(
                "INSERT INTO project_reactions (project_id, user_id, reaction_type) VALUES (?, ?, ?)",
                (project_id, user_id, reaction_type)
            )
            action = "added"
        conn.commit()
        conn.close()
        return JSONResponse(content={"message": f"Reaction {action} successfully", "action": action})
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to handle reaction: {e}")

# --- Profile Routes ---
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    user_data = get_current_user_data(request)
    if not user_data:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("profile.html", {"request": request, "user_data": user_data})

@app.post("/profile/upload-avatar")
async def upload_avatar(request: Request, avatar: UploadFile = File(...)):
    user_data = get_current_user_data(request)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    username = user_data["username"]
    if not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image files are allowed.")
    avatar_filename = f"{username}.png"
    avatar_path = AVATAR_DIR / avatar_filename
    try:
        with open(avatar_path, "wb") as buffer:
            await avatar.seek(0)
            contents = await avatar.read()
            buffer.write(contents)
        conn = get_db_connection()
        cursor = conn.cursor()
        new_avatar_url = f"/static/assets/avatars/{avatar_filename}"
        try:
            cursor.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (new_avatar_url, user_data["id"]))
            conn.commit()
        finally:
            conn.close()
        return RedirectResponse(url="/profile?success=Avatar+uploaded", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        print(f"Error uploading avatar: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload avatar.")

@app.post("/profile/edit", response_class=HTMLResponse)
async def profile_edit(request: Request, username: str = Form(...), email: str = Form(...)):
    user_data = get_current_user_data(request)
    if not user_data:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    user_id = user_data["id"]
    old_username = user_data["username"]
    sanitized_username = sanitize_input(username).strip()
    sanitized_email = sanitize_input(email).strip()

    if not sanitized_username or not sanitized_email:
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("profile.html", {"request": request, "user_data": user_data, "error": "Username and email cannot be empty."})

    conn = get_db_connection()
    cursor = conn.cursor()

    existing_username = cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (sanitized_username, user_id)).fetchone()
    if existing_username:
        conn.close()
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("profile.html", {"request": request, "user_data": user_data, "error": "Username already taken by another account."})

    existing_email = cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (sanitized_email, user_id)).fetchone()
    if existing_email:
        conn.close()
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("profile.html", {"request": request, "user_data": user_data, "error": "Email already used by another account."})

    try:
        cursor.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", (sanitized_username, sanitized_email, user_id))
        conn.commit()

        if sanitized_username != old_username:
            old_avatar_path = AVATAR_DIR / f"{old_username}.png"
            new_avatar_path = AVATAR_DIR / f"{sanitized_username}.png"
            if old_avatar_path.exists():
                old_avatar_path.replace(new_avatar_path)
                cursor.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (f"/static/assets/avatars/{new_avatar_path.name}", user_id))
                conn.commit()
            old_user_dir = USER_DATA_DIR / old_username
            new_user_dir = USER_DATA_DIR / sanitized_username
            if old_user_dir.exists():
                old_user_dir.replace(new_user_dir)

        conn.close()
        return RedirectResponse(url="/profile?success=Profile+updated", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Error updating profile:", e)
        user_data = get_current_user_data(request)
        return templates.TemplateResponse("profile.html", {"request": request, "user_data": user_data, "error": "Failed to update profile. Please try again."})

@app.get("/api/project/{project_id}", response_class=JSONResponse)
async def get_project_api(request: Request, project_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    project = cursor.execute("""
        SELECT p.*, u.username as author_username 
        FROM projects p 
        JOIN users u ON p.author_id = u.id 
        WHERE p.id = ?
    """, (project_id,)).fetchone()
    
    conn.close()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return JSONResponse(content={
        "id": project["id"],
        "title": project["title"],
        "date": project["date_created"],
        "description": project["description"],
        "short_description": project["short_description"],
        "type": project["type"],
        "image_url": project["image_url"],
        "author_username": project["author_username"]
    })

# --- NEW FORUM ROUTES ---

@app.get("/forum", response_class=HTMLResponse)
async def forum_home(request: Request):
    user_data = get_current_user_data(request)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get categories with boards and their stats
    categories_db = cursor.execute("""
        SELECT 
            c.id, c.name, c.display_order,
            b.id as board_id, b.name as board_name, b.description,
            COUNT(DISTINCT t.id) as topic_count,
            COUNT(DISTINCT p.id) as post_count
        FROM forum_categories c
        LEFT JOIN forum_boards b ON c.id = b.category_id
        LEFT JOIN forum_topics t ON b.id = t.board_id
        LEFT JOIN forum_posts p ON t.id = p.topic_id
        GROUP BY c.id, b.id
        ORDER BY c.display_order, b.display_order
    """).fetchall()

    # Get overview stats
    stats = cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM forum_topics) as total_topics,
            (SELECT COUNT(*) FROM forum_posts) as total_posts,
            (SELECT COUNT(*) FROM users) as total_members,
            (SELECT username FROM users ORDER BY created_at DESC LIMIT 1) as newest_member
    """).fetchone()

    # Process categories and boards
    categories = {}
    for row in categories_db:
        if row['id'] not in categories:
            categories[row['id']] = {
                'id': row['id'],
                'name': row['name'],
                'boards': []
            }
        if row['board_id']:
            categories[row['id']]['boards'].append({
                'id': row['board_id'],
                'name': row['board_name'],
                'description': row['description'],
                'topic_count': row['topic_count'] or 0,
                'post_count': row['post_count'] or 0
            })

    conn.close()

    return templates.TemplateResponse("forum/forum_home.html", {
        "request": request,
        "user_data": user_data,
        "categories": list(categories.values()),
        "total_topics": stats['total_topics'],
        "total_posts": stats['total_posts'],
        "total_members": stats['total_members'],
        "newest_member": stats['newest_member'] or "No members yet",
        "latest_news": {
            "text": "Welcome to our new forum!",
            "link": "#"
        }
    })

@app.get("/forum/board/{board_id}", response_class=HTMLResponse)
async def forum_board_detail(request: Request, board_id: int):
    user_data = get_current_user_data(request)
    conn = get_db_connection()
    cursor = conn.cursor()

    board = cursor.execute("SELECT id, name, description FROM forum_boards WHERE id = ?", (board_id,)).fetchone()
    if not board:
        conn.close()
        raise HTTPException(status_code=404, detail="Board not found")
    
    def format_datetime(dt_str):
        try:
            # Parse the datetime string
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            # Store all times in UTC
            dt = dt.replace(tzinfo=timezone.utc)
            # Convert to local timezone for display
            local_dt = dt.astimezone()
            return local_dt.strftime('%b %d, %Y %H:%M')
        except Exception as e:
            print(f"Date formatting error: {e}")
            return dt_str

    # Update query to include post counts and last post info
    # In the board_detail route
    topics_db = cursor.execute("""
        SELECT 
            t.*,
            u.username as author_username,
            (SELECT COUNT(*) FROM forum_posts WHERE topic_id = t.id) - 1 as reply_count,
            (SELECT MAX(created_at) FROM forum_posts WHERE topic_id = t.id) as last_post_date,
            (SELECT username FROM users WHERE id = (
                SELECT user_id FROM forum_posts 
                WHERE topic_id = t.id 
                ORDER BY created_at DESC LIMIT 1
            )) as last_post_author
        FROM forum_topics t
        JOIN users u ON t.user_id = u.id
        WHERE t.board_id = ?
        ORDER BY last_post_date DESC NULLS LAST
    """, (board_id,)).fetchall()

    topics_list = []
    for topic_row in topics_db:
        topic_dict = dict(topic_row)
        # Format dates using the same function as topic detail
        if topic_dict["last_post_date"]:
            topic_dict["last_post_date"] = format_datetime(topic_dict["last_post_date"])
        if topic_dict["created_at"]:
            topic_dict["created_at"] = format_datetime(topic_dict["created_at"])
        topics_list.append(topic_dict)
    
    conn.close()

    return templates.TemplateResponse("forum/board_detail.html", {
        "request": request,
        "user_data": user_data,
        "board": dict(board),
        "topics": topics_list
    })

@app.get("/forum/board/{board_id}/new-topic", response_class=HTMLResponse)
async def new_topic_get(request: Request, board_id: int):
    user_data = get_current_user_data(request)
    if not user_data:
        request.session["redirect_after_login"] = f"/forum/board/{board_id}/new-topic"
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    conn = get_db_connection()
    board = conn.execute("SELECT id, name FROM forum_boards WHERE id = ?", (board_id,)).fetchone()
    conn.close()

    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    return templates.TemplateResponse("forum/new_topic.html", {
        "request": request,
        "user_data": user_data,
        "board": dict(board)
    })

@app.post("/forum/board/{board_id}/new-topic", response_class=RedirectResponse)
async def new_topic_post(
    request: Request,
    board_id: int,
    title: str = Form(...),
    post_text: str = Form(...)
):
    user_id = get_current_user_id(request)
    if not user_id:
        request.session["redirect_after_login"] = f"/forum/board/{board_id}/new-topic"
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    conn = get_db_connection()
    cursor = conn.cursor()

    board = cursor.execute("SELECT id FROM forum_boards WHERE id = ?", (board_id,)).fetchone()
    if not board:
        conn.close()
        raise HTTPException(status_code=404, detail="Board not found")
    
    sanitized_title = sanitize_input(title)
    sanitized_post_text = sanitize_input(post_text) # Basic sanitization, consider Markdown rendering library

    try:
        # Create the topic
        cursor.execute(
            "INSERT INTO forum_topics (board_id, user_id, title) VALUES (?, ?, ?)",
            (board_id, user_id, sanitized_title)
        )
        topic_id = cursor.lastrowid

        # Create the first post in the topic
        cursor.execute(
            "INSERT INTO forum_posts (topic_id, user_id, post_text) VALUES (?, ?, ?)",
            (topic_id, user_id, sanitized_post_text)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error creating new topic: {e}")
        # Redirect back to new topic form with an error (need to pass error to template)
        return RedirectResponse(url=f"/forum/board/{board_id}/new-topic?error=Failed+to+create+topic.", status_code=status.HTTP_302_FOUND)
    finally:
        conn.close()

    return RedirectResponse(url=f"/forum/topic/{topic_id}", status_code=status.HTTP_302_FOUND)


@app.get("/forum/topic/{topic_id}", response_class=HTMLResponse)
async def forum_topic_detail(request: Request, topic_id: int):
    user_data = get_current_user_data(request)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Only increment view if coming from board page or direct link
    referer = request.headers.get('referer', '')
    user_ip = request.client.host
    
    # Get current views count first
    views_count = cursor.execute("""
        SELECT COUNT(DISTINCT user_ip) as unique_views 
        FROM topic_views 
        WHERE topic_id = ?
    """, (topic_id,)).fetchone()["unique_views"]

    if 'board' in referer or not referer:
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Insert or update view record
            cursor.execute("""
                INSERT INTO topic_views (topic_id, user_ip, last_viewed)
                VALUES (?, ?, ?)
                ON CONFLICT(topic_id, user_ip) 
                DO UPDATE SET last_viewed = ?
                WHERE datetime(last_viewed) < datetime('now', '-5 minutes')
            """, (topic_id, user_ip, now, now))
            
            # Update topic views to match unique viewers
            cursor.execute("""
                UPDATE forum_topics 
                SET views = (
                    SELECT COUNT(DISTINCT user_ip) 
                    FROM topic_views 
                    WHERE topic_id = ?
                )
                WHERE id = ?
            """, (topic_id, topic_id))
            
            conn.commit()
        except Exception as e:
            print(f"Error updating view count: {e}")
            conn.rollback()

    topic = cursor.execute(
        """
        SELECT ft.id, ft.title, ft.created_at, ft.views,
               u.username AS author_username, ft.user_id AS author_id,
               fb.id AS board_id, fb.name AS board_name
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        JOIN forum_boards fb ON ft.board_id = fb.id
        WHERE ft.id = ?
        """,
        (topic_id,)
    ).fetchone()

    if not topic:
        conn.close()
        raise HTTPException(status_code=404, detail="Topic not found")

    posts_db = cursor.execute(
        """
        SELECT fp.id, fp.post_text, fp.created_at, fp.updated_at,
               u.username AS author_username, u.id AS user_id,
               u.avatar_url AS author_avatar_url
        FROM forum_posts fp
        JOIN users u ON fp.user_id = u.id
        WHERE fp.topic_id = ?
        ORDER BY fp.created_at ASC
        """,
        (topic_id,)
    ).fetchall()

    def format_datetime(dt_str):
        try:
            # Parse the datetime string
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            # Get the local timezone
            local_tz = datetime.now().astimezone().tzinfo
            # Convert to local time
            local_dt = dt.replace(tzinfo=timezone.utc).astimezone(local_tz)
            return local_dt.strftime('%b %d, %Y %H:%M')
        except Exception as e:
            print(f"Date formatting error: {e}")
            return dt_str

    posts_list = []
    for post_row in posts_db:
        post_dict = dict(post_row)
        if post_dict["created_at"]:
            post_dict["created_at"] = format_datetime(post_dict["created_at"])
        if post_dict["updated_at"]:
            post_dict["updated_at"] = format_datetime(post_dict["updated_at"])
        
        # Handle avatar URL (similar to get_current_user_data)
        author_avatar = post_dict["author_avatar_url"]
        if not author_avatar:
             author_avatar = "/static/assets/images/default-avatar.png"
        elif author_avatar.startswith("/static/assets/avatars/"):
            avatar_file = AVATAR_DIR / Path(author_avatar).name
            if not avatar_file.exists():
                author_avatar = "/static/assets/images/default-avatar.png"
        post_dict["author_avatar"] = author_avatar
        posts_list.append(post_dict)

    conn.close()

    topic_dict = dict(topic)
    if topic_dict["created_at"]:
        topic_dict["created_at"] = datetime.strptime(topic_dict["created_at"], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %H:%M')

    return templates.TemplateResponse("forum/topic_detail.html", {
        "request": request,
        "user_data": user_data,
        "topic": topic_dict,
        "board": {"id": topic_dict["board_id"], "name": topic_dict["board_name"]},
        "posts": posts_list,
        "is_admin": is_admin_user(request)
    })

@app.post("/forum/topic/{topic_id}/reply", response_class=RedirectResponse)
async def reply_to_topic(topic_id: int, request: Request, post_text: str = Form(...)):
    user_id = get_current_user_id(request)
    if not user_id:
        request.session["redirect_after_login"] = f"/forum/topic/{topic_id}"
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get topic info for notifications
        topic = cursor.execute("SELECT title FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO forum_posts (topic_id, user_id, post_text, created_at) VALUES (?, ?, ?, ?)",
            (topic_id, user_id, post_text, now)
        )
        new_post_id = cursor.lastrowid

        # Handle mentions
        mentioned_users = extract_mentions(post_text)
        if mentioned_users:
            for username in mentioned_users:
                user = cursor.execute(
                    "SELECT id FROM users WHERE username = ?", 
                    (username,)
                ).fetchone()
                if user and user["id"] != user_id:  # Don't notify self-mentions
                    create_mention_notification(
                        cursor, user["id"], user_id, new_post_id, topic_id, topic["title"]
                    )

        conn.commit()
        return RedirectResponse(url=f"/forum/topic/{topic_id}#post-{new_post_id}", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/forum/boards/{category_id}")
async def get_boards_by_category(category_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        boards = cursor.execute("""
            SELECT b.id, b.name, b.description 
            FROM forum_boards b
            WHERE b.category_id = ?
            ORDER BY b.display_order
        """, (category_id,)).fetchall()
        
        return [dict(board) for board in boards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/forum/post/{post_id}/edit")
async def edit_forum_post(request: Request, post_id: int, post_text: str = Form(...)):
    user_data = get_current_user_data(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    post = cursor.execute("""
        SELECT p.*, t.id as topic_id 
        FROM forum_posts p
        JOIN forum_topics t ON p.topic_id = t.id
        WHERE p.id = ?
    """, (post_id,)).fetchone()
    
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["user_id"] != user_data["id"] and not is_admin_user(request):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get current time in local timezone
        local_now = datetime.now().astimezone()
        # Convert to UTC for storage
        utc_now = local_now.astimezone(timezone.utc)
        
        cursor.execute(
            "UPDATE forum_posts SET post_text = ?, updated_at = ? WHERE id = ?",
            (post_text, utc_now.strftime('%Y-%m-%d %H:%M:%S'), post_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/forum/post/{post_id}/delete")
async def delete_forum_post(request: Request, post_id: int):
    user_data = get_current_user_data(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get post info including if it's the first post
        post = cursor.execute("""
            SELECT p.*, 
                   (SELECT MIN(id) FROM forum_posts WHERE topic_id = p.topic_id) as first_post_id
            FROM forum_posts p 
            WHERE p.id = ?
        """, (post_id,)).fetchone()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
            
        # Only allow delete if user is author or admin
        if post["user_id"] != user_data["id"] and not is_admin_user(request):
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
            
        # Don't allow deletion of first post in topic
        if post["id"] == post["first_post_id"]:
            raise HTTPException(status_code=403, detail="Cannot delete the first post of a topic")
        
        cursor.execute("DELETE FROM forum_posts WHERE id = ?", (post_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/forum/create-topic")
async def create_topic_api(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),  # Changed from post_text to match frontend
    board_id: int = Form(...)
):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current time in local timezone and convert to UTC for storage
        local_now = datetime.now().astimezone()
        utc_now = local_now.astimezone(timezone.utc)
        now = utc_now.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            "INSERT INTO forum_topics (board_id, user_id, title, created_at, updated_at, views) VALUES (?, ?, ?, ?, ?, 0)",
            (board_id, user_id, title, now, now)
        )
        topic_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO forum_posts (topic_id, user_id, post_text, created_at) VALUES (?, ?, ?, ?)",
            (topic_id, user_id, content, now)
        )
        
        conn.commit()
        return {"topic_id": topic_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/forum/post/{post_id}")
async def delete_forum_post(request: Request, post_id: int):
    user_data = get_current_user_data(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM forum_posts WHERE id = ? AND user_id = ?", (post_id, user_data['id']))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/forum/topic/{topic_id}/delete")
async def delete_forum_topic(request: Request, topic_id: int):
    user_data = get_current_user_data(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user is topic author
        topic = cursor.execute("""
            SELECT user_id, board_id FROM forum_topics WHERE id = ?
        """, (topic_id,)).fetchone()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
            
        if topic["user_id"] != user_data["id"] and not is_admin_user(request):
            raise HTTPException(status_code=403, detail="Not authorized to delete this topic")
        
        # Delete all posts first (due to foreign key constraints)
        cursor.execute("DELETE FROM forum_posts WHERE topic_id = ?", (topic_id,))
        
        # Delete the topic
        cursor.execute("DELETE FROM forum_topics WHERE id = ?", (topic_id,))
        
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

def extract_mentions(text: str) -> list:
    """Extract usernames from @mentions in text"""
    import re
    mentions = re.findall(r'@(\w+)', text)
    return list(set(mentions))  # Remove duplicates

def create_mention_notification(cursor, mentioned_user_id: int, source_user_id: int, post_id: int, topic_id: int, topic_title: str):
    """Create a notification for mentioned user"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO notifications (
            user_id, type, content, link, source_id, source_type, source_user_id, created_at
        ) VALUES (?, 'mention', ?, ?, ?, 'forum_post', ?, ?)
    """, (
        mentioned_user_id,
        f"You were mentioned in topic: {topic_title}",
        f"/forum/topic/{topic_id}#post-{post_id}",
        post_id,
        source_user_id,
        now
    ))

@app.get("/api/notifications")
async def get_notifications(request: Request):
    user_data = get_current_user_data(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    notifications = cursor.execute("""
        SELECT n.*, u.username as source_username, u.avatar_url as source_avatar_url
        FROM notifications n
        LEFT JOIN users u ON n.source_user_id = u.id
        WHERE n.user_id = ? AND n.is_read = 0
        ORDER BY n.created_at DESC
        LIMIT 50
    """, (user_data["id"],)).fetchall()
    
    conn.close()
    return [dict(n) for n in notifications]

