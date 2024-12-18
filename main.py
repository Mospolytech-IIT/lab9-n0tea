"""Главный файл со всеми crud запросами и выводом html форм"""
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import Base, User, Post
from connect_database import engine, SessionLocal

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

# Добавление данных
@app.get("/users/create/", response_class=HTMLResponse)
async def create_user_form(request: Request):
    """вывод формы отдельно от самой рабочей функции"""
    return templates.TemplateResponse("user_form.html", {"request": request})

@app.post("/users/create/")
async def create_user(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """создать пользователя основываясь на значениях из формы"""
    existing_user = db.query(User).filter_by(email=email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    db_user = User(username=username, email=email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return RedirectResponse(url="/", status_code=303)

@app.get("/posts/create/", response_class=HTMLResponse)
async def create_post_form(request: Request, user_id: int):
    """вывод формы отдельно от самой рабочей функции"""
    return templates.TemplateResponse("post_form.html", {"request": request, "user_id": user_id})

@app.post("/posts/create/")
async def create_post(title: str = Form(...), content: str = Form(...), user_id: int = Form(...), db: Session = Depends(get_db)):
    """создать пост для пользователя по id"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_post = Post(title=title, content=content, user_id=user_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return RedirectResponse(url=f"/users/{user_id}/posts/", status_code=303)

# Извлечение данных
@app.get("/", response_class=HTMLResponse)
async def get_users_page(request: Request, db: Session = Depends(get_db)):
    """корень открывает пользователей, все записи из таблицы users"""
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@app.get("/users/{user_id}/posts/", response_class=HTMLResponse)
async def view_user_posts(request: Request, user_id: int, db: Session = Depends(get_db)):
    """получает все посты конкретного пользователя."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = db.query(Post).filter_by(user_id=user_id).all()
    return templates.TemplateResponse("posts.html", {"request": request, "user": user, "posts": posts})
@app.get("/posts/")
def read_posts(db: Session = Depends(get_db)):
    """получает все посты с информацией о пользователях, которые их создали"""
    # joinedload приколтный
    posts = db.query(Post).options(joinedload(Post.user)).all()
    return posts

# Обновление данных (тут как и у delete пришлось убрать put (его нет в html))
@app.get("/posts/{post_id}/edit/", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int, db: Session = Depends(get_db)):
    """вывод формы отдельно, по id поста"""

    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("post_form.html", {"request": request, "post": post, "user_id": post.user_id})

@app.post("/posts/{post_id}/edit/")
async def edit_post(post_id: int, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    """редактировать пост"""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.title = title
    post.content = content
    db.commit()
    db.refresh(post)
    return RedirectResponse(url=f"/users/{post.user_id}/posts/", status_code=303)

@app.get("/users/{user_id}/edit/", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    """вывод формы отдельно, по id пользователя"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_form.html", {"request": request, "user": user})

@app.post("/users/{user_id}/edit/")
async def edit_user(user_id: int, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """редактировать пользователя"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = username
    user.email = email
    user.password = password
    db.commit()
    db.refresh(user)
    return RedirectResponse(url="/", status_code=303)

# Удаление данных (пришлось использовать post а не delete чтобы заработали формы из 3 задания)
@app.post("/users/{user_id}/")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """удаление пользователя и всех постов его"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(Post).filter_by(user_id=user_id).delete()
    db.delete(user)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/posts/{post_id}/")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """удаление поста"""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return RedirectResponse(url=f"/users/{post.user_id}/posts/", status_code=303)

# Запуск приложения, если не юзать uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
