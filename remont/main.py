#MAINNNNNNN
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import qrcode
import io

from db import get_db
from models import User, Role, Request, Comment
from schemas import (
    LoginSchema, RegisterSchema,
    RequestCreateSchema, RequestUpdateSchema,
    CommentCreateSchema, ExtendDeadlineSchema
)

app = FastAPI(title="Учет заявок на ремонт бытовой техники")


ROLE_MAP = {
    "заказчик": "client",
    "оператор": "operator",
    "мастер": "specialist",
    "менеджер": "manager",
    "администратор": "admin",
}


def get_current_user(
    x_user_id: int = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    user = db.query(User).get(x_user_id)
    if not user:
        raise HTTPException(401, "Пользователь не найден")
    return user


def role_name(user: User) -> str:
    return ROLE_MAP.get(user.role.name, user.role.name)



@app.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.login == data.login,
        User.password == data.password
    ).first()

    if not user:
        raise HTTPException(401, "Неверный логин или пароль")

    return {
        "id": user.id,
        "fio": user.fio,
        "role": role_name(user)
    }


@app.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.name == "заказчик").first()
    if not role:
        raise HTTPException(500, "Роль заказчика не найдена")

    user = User(
        fio=data.fio,
        phone=data.phone,
        login=data.login,
        password=data.password,
        role_id=role.id
    )
    db.add(user)
    db.commit()

    return {"status": "ok"}



@app.get("/requests")
def get_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Request)

    if role_name(user) == "client":
        q = q.filter(Request.client_id == user.id)

    if role_name(user) == "specialist":
        q = q.filter(Request.master_id == user.id)

    items = q.order_by(Request.id).all()

    return [
        {
            "id": r.id,
            "status": r.status,
            "climate_tech_type": r.appliance_type,
            "climate_tech_model": r.appliance_model,
            "problem_description": r.problem_description,
            "client_fio": r.client.fio if r.client else None,
            "client_phone": r.client.phone if r.client else None,
            "master_fio": r.master.fio if r.master else None,
        }
        for r in items
    ]


@app.get("/requests/search")
def search_requests(
    q: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Request).filter(
        Request.appliance_type.ilike(f"%{q}%") |
        Request.appliance_model.ilike(f"%{q}%") |
        Request.problem_description.ilike(f"%{q}%")
    )
    return get_requests(user, db)


@app.post("/requests")
def create_request(
    data: RequestCreateSchema,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if role_name(user) != "client":
        raise HTTPException(403, "Только заказчик может создавать заявки")

    req = Request(
        start_date=date.today(),
        appliance_type=data.climate_tech_type,
        appliance_model=data.climate_tech_model,
        problem_description=data.problem_description,
        status="Новая заявка",
        client_id=user.id
    )
    db.add(req)
    db.commit()
    return {"request_id": req.id}


@app.put("/requests/{rid}")
def update_request(
    rid: int,
    data: RequestUpdateSchema,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if role_name(user) not in ("operator", "manager", "admin"):
        raise HTTPException(403, "Недостаточно прав")

    req = db.query(Request).get(rid)
    if not req:
        raise HTTPException(404, "Заявка не найдена")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(req, field, value)

    db.commit()
    return {"status": "ok"}


@app.put("/requests/extend")
def extend_request(
    data: ExtendDeadlineSchema,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if role_name(user) not in ("manager", "admin"):
        raise HTTPException(403, "Недостаточно прав")

    req = db.query(Request).get(data.request_id)
    if not req:
        raise HTTPException(404, "Заявка не найдена")

    req.completion_date = data.new_date
    db.commit()
    return {"status": "ok"}



@app.post("/comments")
def add_comment(
    data: CommentCreateSchema,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if role_name(user) not in ("specialist", "operator", "manager", "admin"):
        raise HTTPException(403, "Недостаточно прав")

    com = Comment(
        request_id=data.request_id,
        user_id=user.id,
        message=data.message
    )
    db.add(com)
    db.commit()
    return {"status": "ok"}



@app.get("/stats")
def stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if role_name(user) not in ("manager", "admin"):
        raise HTTPException(403, "Недостаточно прав")

    done = db.query(Request).filter(Request.status.ilike("%Готов%")).count()

    avg_days = db.query(
        func.avg(Request.completion_date - Request.start_date)
    ).scalar() or 0

    by_type = db.query(
        Request.appliance_type, func.count()
    ).group_by(Request.appliance_type).all()

    return {
        "done_count": done,
        "avg_days": float(avg_days),
        "by_equipment_type": [
            {"name": t, "count": c} for t, c in by_type
        ],
        "by_problem_keywords": []
    }



@app.get("/feedback/qr")
def feedback_qr():
    img = qrcode.make("Спасибо за оценку качества обслуживания!")
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return buf.read()
