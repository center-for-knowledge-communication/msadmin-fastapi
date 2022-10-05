## uvicorn main:app --reload
import json
from fastapi import FastAPI, Request, Response, status, Depends, Query, Form, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session
from fastapi_login import LoginManager
from typing import Optional, List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timedelta
from db import SessionLocal, engine, DBContext
# from fakeuser import users
from fakedb import *
import models, crud, schemas
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

manager = LoginManager(secret=SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth_token"

def get_db():
    with DBContext() as db:
        yield db

@manager.user_loader()
def get_user_from_db(username: str, db: Session = None):
    if db is None:
        with DBContext() as db:
            return crud.get_user_by_username(db=db, username=username)
    return crud.get_user_by_username(db=db, username=username)
    # if username in users.keys():
    #     return UserDB(**users[username])

password_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_hashed_password(plain_password: str):
    return password_ctx.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str):
    return password_ctx.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    if not user:
        return None
    if not verify_password(plain_password=password, hashed_password=user.password):
        return None
    return user
 
# class User(BaseModel):
#     username: str
#     email: str
#     first_name: str
#     last_name: str
#     last_login: Optional[str]
#     date_joined: str 
#     is_superuser: int
#     is_staff: int
#     is_active: Optional[int] = 1
#     # notifications: List[Notifications] = []

# class UserDB(User):
#     id: int
#     password: str

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    # if not logged in, this will be the page. If logged in, redirect to /home
    # if not user:
    #     return templates.TemplateResponse("index.html", {"request": request, "title": "MathSpring Admin Tool - Home"})
    return RedirectResponse("/home", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "MathSpring Admin Tool - Login", "invalid": False})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db=db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "title": "MathSpring Admin Tool - Login", "invalid": True}, status_code=status.HTTP_401_UNAUTHORIZED)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = manager.create_access_token(data={"sub":user.username}, expires=access_token_expires)
    crud.update_user_last_login(db=db, user=user)
    response = RedirectResponse("/home", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(response, access_token)
    return response

class NotAuthenticatedException(Exception):
    pass

def not_authenticated_exception_handler(request: Request, exception: NotAuthenticatedException):
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
 
manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(NotAuthenticatedException, not_authenticated_exception_handler)

@app.get("/home")
async def home(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    # return jsonable_encoder(user)
    return templates.TemplateResponse("home.html", {"request": request, "title": "MathSpring Admin Tool - Home", "user": user})

@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse("/")
    manager.set_cookie(response, None)
    return response

@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    if user.is_superuser or user.is_staff:
        return templates.TemplateResponse("utilities/register.html", {"request": request, "title": "MathSpring Admin Tool - Create Account", "user": user})
    else:
        return RedirectResponse("/notauthorized", status_code=status.HTTP_302_FOUND)
    
@app.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), is_superuser: int = Form(...), is_staff: int = Form(...), is_active = 1, password: str = Form(...), password_confirm: str = Form(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    hashed_password = get_hashed_password(password)
    invalid_user = False
    invalid_email = False
    if crud.get_user_by_username(db=db, username=username):
        invalid_user = True
    if crud.get_user_by_email(db=db, email=email):
        invalid_email = True

    invalid_password = (len(password) < 10 or (not password.isalnum()))
    password_not_match = (password != password_confirm)

    if invalid_user or invalid_email or invalid_password or password_not_match:
        return templates.TemplateResponse("utilities/register.html", {"request": request, "title": "MathSpring Admin Tool - Create Account", "invalid_user": invalid_user, "invalid_email": invalid_email, "invalid_password": invalid_password, "password_not_match": password_not_match, "user":user}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        crud.create_user(db=db,user=schemas.UserCreate(username=username, email=email, first_name=first_name, last_name=last_name, is_superuser=is_superuser, is_staff=is_staff, is_active=is_active, password=hashed_password, date_joined=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        response = RedirectResponse("/utilities", status_code=status.HTTP_302_FOUND)
        return response

@app.get("/notauthorized", response_class=HTMLResponse)
async def not_authorized(request: Request, user: schemas.User = Depends(manager), db: Session = Depends(get_db)):
    return templates.TemplateResponse("notauthorized.html", {"request": request, "title": "MathSpring Admin Tool - Not Authorized", "user": user})

@app.get("/problem", response_class=HTMLResponse)
async def get_problems(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    # user = User(**dict(user))
    return templates.TemplateResponse("problem.html", {"request": request, "title": "MathSpring Admin Tool - Math Problems", "user": user})

@app.get("/topic", response_class=HTMLResponse)
async def get_topics(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("topic.html", {"request": request, "title": "MathSpring Admin Tool - Math Topics", "user": user})

@app.get("/survey", response_class=HTMLResponse)
async def get_users(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("survey.html", {"request": request, "title": "MathSpring Admin Tool - Surveys", "user": user})

@app.get("/standard", response_class=HTMLResponse)
async def get_tools(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("standard.html", {"request": request, "title": "MathSpring Admin Tool - Tools", "user": user})

@app.get("/strategies", response_class=HTMLResponse)
async def get_strategies(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("strategies.html", {"request": request, "title": "MathSpring Admin Tool - Strategies", "user": user})

@app.get("/utilities", response_class=HTMLResponse)
async def get_utilities(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    if user.is_superuser or user.is_staff:
        return templates.TemplateResponse("utilities.html", {"request": request, "title": "MathSpring Admin Tool - Utilities", "user": user})
    else:
        return RedirectResponse("/notauthorized", status_code=status.HTTP_302_FOUND)
    
@app.get("/usertable", response_class=HTMLResponse)
async def get_usertable(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    if (not user.is_superuser):
        return RedirectResponse("/notauthorized", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("utilities/usertable.html", {"request": request, "title": "MathSpring Admin Tool - User Table", "user": user})

@app.get("/usertable/edit", response_class=HTMLResponse)
async def get_usertable_edit_query(request: Request, id: int = Query(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    if (not user.is_superuser):
        return RedirectResponse("/notauthorized", status_code=status.HTTP_302_FOUND)
    modify_user = crud.get_user_by_id(db=db, user_id=id)
    return templates.TemplateResponse("utilities/edit.html", {"request": request, "title": "MathSpring Admin Tool - User Table", "user": user, "modify_user": modify_user})

@app.get("/usertable/edit/{id}", response_class=HTMLResponse)
async def get_usertable_edit(request: Request, id: int = Path(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    if (not user.is_superuser):
        return RedirectResponse("/notauthorized", status_code=status.HTTP_302_FOUND)
    modify_user = crud.get_user_by_id(db=db, user_id=id)
    if not modify_user:
        return RedirectResponse("/usertable", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("utilities/edit.html", {"request": request, "title": "MathSpring Admin Tool - User Table - Edit", "user": user, "modify_user": modify_user})

@app.post("/usertable/edit/{id}", response_class=HTMLResponse)
async def post_usertable_edit(request: Request, id: int = Path(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager), username: str = Form(...), email: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), is_superuser: bool = Form(...), is_staff: bool = Form(...)):
    modify_user = crud.get_user_by_id(db=db, user_id=id)
    if not modify_user:
        return RedirectResponse("/usertable", status_code=status.HTTP_302_FOUND)
    invalid_username = False
    invalid_email = False
    if crud.get_user_by_username(db=db, username=username) and (crud.get_user_by_username(db=db, username=username).username != modify_user.username):
        invalid_username = True
    if crud.get_user_by_email(db=db, email=email) and (crud.get_user_by_email(db=db, email=email).email != modify_user.email):
        invalid_email = True
    if invalid_username or invalid_email:
        return templates.TemplateResponse("utilities/edit.html", {"request": request, "title": "MathSpring Admin Tool - User Table - Edit", "user": user, "modify_user": modify_user, "invalid_username": invalid_username, "invalid_email": invalid_email}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        crud.update_user_all(db=db, user=modify_user, username=username, email=email, first_name=first_name, last_name=last_name, is_superuser=is_superuser, is_staff=is_staff)
        return RedirectResponse("/usertable", status_code=status.HTTP_302_FOUND)

@app.get("/usertable/delete/{id}", response_class=HTMLResponse)
async def post_usertable_delete(request: Request, id: int = Path(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    if (not user.is_superuser):
        return RedirectResponse("/notauthorized", status_code=status.HTTP_302_FOUND)
    modify_user = crud.get_user_by_id(db=db, user_id=id)
    if not modify_user:
        return RedirectResponse("/usertable", status_code=status.HTTP_302_FOUND)
    crud.delete_user_by_id(db=db, user=modify_user)
    return RedirectResponse("/usertable", status_code=status.HTTP_302_FOUND)

@app.get("/user", response_class=HTMLResponse)
async def get_users(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("user.html", {"request": request, "title": "MathSpring Admin Tool - Users: "+user.username, "user": user})

@app.get("/changepassword", response_class=HTMLResponse)
async def get_change_password(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("user/changepassword.html", {"request": request, "title": "MathSpring Admin Tool - Change Password", "user": user})

@app.post("/changepassword", response_class=HTMLResponse)
async def post_changepassword(request: Request, current_password: str = Form(...), password: str = Form(...), password_confirm: str = Form(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    hashed_password = get_hashed_password(password)
    invalid_password = (len(password) < 10 or (not password.isalnum()))
    password_not_match = (password != password_confirm)
    wrong_password = not verify_password(plain_password=current_password, hashed_password=user.password)
    if invalid_password or password_not_match or wrong_password:
        return templates.TemplateResponse("user/changepassword.html", {"request": request, "title": "MathSpring Admin Tool - Create Account", "wrong_password": wrong_password,"invalid_password": invalid_password, "password_not_match": password_not_match, "user": user}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        crud.update_user_password(db=db, user=user, password=hashed_password)
        response = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(response, None)
        return response

@app.get("/changename", response_class=HTMLResponse)
async def get_change_name(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("user/changename.html", {"request": request, "title": "MathSpring Admin Tool - Change Name", "user": user})

@app.post("/changename", response_class=HTMLResponse)
async def post_change_name(request: Request, first_name: str = Form(...), last_name: str = Form(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    crud.update_user_name(db=db, user=user, first_name=first_name, last_name=last_name)
    response = RedirectResponse("/user", status_code=status.HTTP_302_FOUND)
    return response

@app.get("/changeemail", response_class=HTMLResponse)
async def get_change_email(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("user/changeemail.html", {"request": request, "title": "MathSpring Admin Tool - Change Email", "user": user})

@app.post("/changeemail", response_class=HTMLResponse)
async def post_change_email(request: Request, email: str = Form(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    invalid_email = False
    if crud.get_user_by_email(db=db, email=email):
        invalid_email = True
    if invalid_email:
        return templates.TemplateResponse("user/changeemail.html", {"request": request, "title": "MathSpring Admin Tool - Change Email", "invalid_email": invalid_email, "user": user}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        crud.update_user_email(db=db, user=user, email=email)
        response = RedirectResponse("/user", status_code=status.HTTP_302_FOUND)
        return response

@app.get("/changeavatar", response_class=HTMLResponse)
async def get_change_avatar(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("user/changeavatar.html", {"request": request, "title": "MathSpring Admin Tool - Change Avatar", "user": user})

@app.get("/changeusername", response_class=HTMLResponse)
async def get_change_username(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("user/changeusername.html", {"request": request, "title": "MathSpring Admin Tool - Change Username", "user": user})

@app.post("/changeusername", response_class=HTMLResponse)
async def post_change_username(request: Request, username: str = Form(...), db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    invalid_username = False
    if crud.get_user_by_username(db=db, username=username):
        invalid_username = True
    if invalid_username:
        return templates.TemplateResponse("user/changeusername.html", {"request": request, "title": "MathSpring Admin Tool - Change Username", "invalid_username": invalid_username, "user": user}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        crud.update_user_username(db=db, user=user, username=username)
        response = RedirectResponse("/logout", status_code=status.HTTP_302_FOUND)
        return response

@app.get("/test", response_class=HTMLResponse)
async def get_test(request: Request, db: Session = Depends(get_db), user: schemas.User = Depends(manager)):
    return templates.TemplateResponse("test.html", {"request": request, "title": "MathSpring Admin Tool - Test", "user": user})