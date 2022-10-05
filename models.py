from sqlalchemy import String, Integer, Column, ForeignKey, text, create_engine
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "auth_user"
    id = Column(Integer, primary_key=True, unique=True, index=True, nullable=False, autoincrement=True)
    password = Column(String(128), nullable=False) # password is hashed
    last_login = Column(String(128), nullable=True)
    is_superuser = Column(Integer, nullable=False)
    username = Column(String(128), unique=True, index=True, nullable=False)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    email = Column(String(128), unique=True, index=True, nullable=True)
    is_staff = Column(Integer, nullable=False)
    is_active = Column(Integer, nullable=False)
    date_joined = Column(String(128), nullable=False)

class Problem(Base):
    __tablename__ = "problem"
    id = Column(Integer, primary_key=True, unique=True, index=True, nullable=False)
    form = Column(String(128), nullable=True)
    name = Column(String(128), nullable=True)
    nickname = Column(String(128), nullable=True)
    animationResource = Column(String(128), nullable=True)
    answer = Column(String(128), nullable=True)
    audioResource = Column(String(128), nullable=True)
    creator = Column(String(128), nullable=True)
    lastModifier = Column(String(128), nullable=True)
    status = Column(String(128), nullable=True)
    statementHTML = Column(String(128), nullable=True)
    imageURL = Column(String(128), nullable=True)


    

