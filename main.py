"""Главный файл где происходит создание таблиц, а также работа с транзакциями для crud операций"""
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from models import Base, User, Post
from connect_database import engine, SessionLocal
from fastapi.templating import Jinja2Templates
# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates_web")

app = FastAPI()

def get_db():
    """Для создания сессий внутри эндпоинтов"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD операции
# @app.get("/", response_class=HTMLResponse)
# def get_users_page(request: Request, db: Session = Depends(get_db)):
#     """корень открывает пользователей"""
#     users = db.query(User).all()
#     return templates.TemplateResponse("users.html", {"request": request, "users": users})

@app.get("/", response_class=HTMLResponse)
async def get_users_page(request: Request, db: Session = Depends(get_db)):
    """Главная страница со списком всех пользователей"""
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@app.get("/users/create/", response_class=HTMLResponse)
def create_user_form(request: Request):
    return templates.TemplateResponse("user_form.html", {"request": request})

@app.post("/users/create/")
def create_user(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter_by(email=email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    db_user = User(username=username, email=email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return RedirectResponse(url="/", status_code=303)
# поменял на создание с помощью форм
# @app.post("/users/")
# def create_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
#     """Создает нового пользователя"""
#     # Проверка чтобы не было ошибок если одинаковые и не ломалась прога
#     existing_user = db.query(User).filter_by(email=email).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="User with this email already exists")

#     db_user = User(username=username, email=email, password=password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

@app.get("/users/{user_id}/edit/", response_class=HTMLResponse)
def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_form.html", {"request": request, "user": user})
# Добавление
@app.post("/posts/")
def create_post(title: str, content: str, user_id: int, db: Session = Depends(get_db)):
    """Создает новый пост."""
    # существует ли пользователь, к которому будет привязан пост
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_post = Post(title=title, content=content, user_id=user_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


# Получение
@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    """Получает всех пользователей."""
    return db.query(User).all()

@app.get("/posts/")
def read_posts(db: Session = Depends(get_db)):
    """Получает все посты с информацией о пользователях, которые их создали."""
    posts = db.query(Post).options(joinedload(Post.user)).all()
    return posts # тут joinedload прикольно

@app.get("/users/{user_id}/posts/")
def read_user_posts(user_id: int, db: Session = Depends(get_db)):
    """Получает все посты конкретного пользователя."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return db.query(Post).filter_by(user_id=user_id).all()


# Обновление
@app.put("/users/{user_id}/")
def update_user_email(user_id: int, email: str, db: Session = Depends(get_db)):
    """Обновляет email пользователя."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email = email
    db.commit()
    db.refresh(user)
    return user

@app.put("/posts/{post_id}/")
def update_post_content(post_id: int, content: str, db: Session = Depends(get_db)):
    """Обновляет содержание поста."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.content = content
    db.commit()
    db.refresh(post)
    return post


# Удаление
@app.delete("/posts/{post_id}/")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Удаляет пост."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

@app.delete("/users/{user_id}/")
def delete_user_and_posts(user_id: int, db: Session = Depends(get_db)):
    """Удаляет пользователя и все его посты."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(Post).filter_by(user_id=user_id).delete()

    db.delete(user)
    db.commit()
    return {"message": "User and all related posts deleted successfully"}

# Запуск приложения, если не юзать uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

#http://127.0.0.1:8000/docs. тут сваггер с формами
