from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", back_populates="role")



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    fio = Column(String, nullable=False)
    phone = Column(String)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    role = relationship("Role", back_populates="users")

    # связи
    requests_as_client = relationship(
        "Request",
        foreign_keys="Request.client_id",
        back_populates="client"
    )
    requests_as_master = relationship(
        "Request",
        foreign_keys="Request.master_id",
        back_populates="master"
    )
    comments = relationship("Comment", back_populates="user")



class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    start_date = Column(Date, nullable=False)

    appliance_type = Column(String, nullable=False)
    appliance_model = Column(String, nullable=False)
    problem_description = Column(Text, nullable=False)

    status = Column(String, nullable=False)
    completion_date = Column(Date)
    repair_parts = Column(Text)

    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("users.id"))

    client = relationship(
        "User",
        foreign_keys=[client_id],
        back_populates="requests_as_client"
    )
    master = relationship(
        "User",
        foreign_keys=[master_id],
        back_populates="requests_as_master"
    )

    comments = relationship("Comment", back_populates="request")



class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)

    user = relationship("User", back_populates="comments")
    request = relationship("Request", back_populates="comments")
