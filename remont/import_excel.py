import pandas as pd
from sqlalchemy import create_engine


DB_URL = "postgresql://postgres:123@localhost:5432/fa"
engine = create_engine(DB_URL)

BASE_PATH = ""


users_src = pd.read_excel(BASE_PATH + "inputDataUsers.xlsx")

roles = (
    users_src[["type"]]
    .drop_duplicates()
    .rename(columns={"type": "name"})
)

roles["name"] = roles["name"].str.lower()
from sqlalchemy import text

with engine.begin() as conn:
    for role in roles["name"].unique():
        conn.execute(
            text("""
                INSERT INTO roles (name)
                VALUES (:name)
                ON CONFLICT (name) DO NOTHING
            """),
            {"name": role}
        )

roles_db = pd.read_sql("SELECT id, name FROM roles", engine)
role_map = dict(zip(roles_db["name"], roles_db["id"]))


users = users_src.rename(columns={
    "userID": "id",
    "fio": "fio",
    "phone": "phone",
    "login": "login",
    "password": "password",
    "type": "role"
})

users["role"] = users["role"].str.lower()
users["role_id"] = users["role"].map(role_map)

users = users[[
    "id",
    "fio",
    "phone",
    "login",
    "password",
    "role_id"
]]

from sqlalchemy import text

with engine.begin() as conn:
    for _, row in users.iterrows():
        conn.execute(
            text("""
                INSERT INTO users (id, fio, phone, login, password, role_id)
                VALUES (:id, :fio, :phone, :login, :password, :role_id)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": int(row["id"]),
                "fio": row["fio"],
                "phone": row["phone"],
                "login": row["login"],
                "password": row["password"],
                "role_id": int(row["role_id"]),
            }
        )


req = pd.read_excel(BASE_PATH + "inputDataRequests.xlsx")

req = req.rename(columns={
    "problemDescryption": "problem_description",
    "requestStatus": "status",
    "homeTechType": "appliance_type",
    "homeTechModel": "appliance_model",
    "startDate": "start_date",
    "completionDate": "completion_date",
    "repairParts": "repair_parts",
    "masterID": "master_id",
    "clientID": "client_id",
    "requestID": "id"
})

# даты
req["start_date"] = pd.to_datetime(req["start_date"], errors="coerce").dt.date
req["completion_date"] = pd.to_datetime(req["completion_date"], errors="coerce").dt.date

req.to_sql("requests", engine, if_exists="append", index=False)


com = pd.read_excel(BASE_PATH + "inputDataComments.xlsx")

com = com.rename(columns={
    "commentID": "id",
    "message": "message",
    "masterID": "user_id",
    "requestID": "request_id"
})

com.to_sql("comments", engine, if_exists="append", index=False)

print("Импорт данных полностью соответствует SQL и Excel")
