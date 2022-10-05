from datetime import datetime
from sqlalchemy.orm import Session
import models, schemas
import uuid

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # id = uuid.uuid4()
    # while get_user_by_id(db=db, id=int(id)):
    #     id = uuid.uuid4()
    db_users = models.User(username=user.username, email=user.email, first_name=user.first_name, last_name=user.last_name, password=user.password, date_joined=user.date_joined, last_login=user.last_login, is_superuser=user.is_superuser, is_staff=user.is_staff, is_active=user.is_active)
    db.add(db_users)
    db.commit()
    db.refresh(db_users)
    return db_users

def update_user_last_login(db: Session, user: models.User):
    user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    db.refresh(user)
    return user

def update_user_password(db: Session, user: models.User, password: str):
    db_user = get_user_by_id(db=db, user_id=user.id)
    db_user.password = password
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_email(db: Session, user: models.User, email: str):
    db_user = get_user_by_id(db=db, user_id=user.id)
    db_user.email = email
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_name(db: Session, user: models.User, first_name: str, last_name: str):
    db_user = get_user_by_id(db=db, user_id=user.id)
    db_user.first_name = first_name
    db_user.last_name = last_name
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_username(db: Session, user: models.User, username: str):
    db_user = get_user_by_id(db=db, user_id=user.id)
    db_user.username = username
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_all(db: Session, user: models.User, username: str, email: str, first_name: str, last_name: str, is_superuser: bool, is_staff: bool):
    db_user = get_user_by_id(db=db, user_id=user.id)
    db_user.username = username
    db_user.email = email
    db_user.first_name = first_name
    db_user.last_name = last_name
    db_user.is_superuser = is_superuser
    db_user.is_staff = is_staff
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user_by_id(db: Session, user: models.User):
    delete_id = user.id
    print(delete_id)
    db.query(models.User).filter(models.User.id == delete_id).delete()
    db.commit()

def get_problem_by_id(db: Session, problem_id: int):
    return db.query(models.Problem).filter(models.Problem.id == problem_id).first()