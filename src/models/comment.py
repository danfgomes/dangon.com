from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.post import Post



class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int]= mapped_column(primary_key=True)
    author_id: Mapped[int]  = mapped_column(ForeignKey("users.id"))
    post_id: Mapped["Post"] = relationship("Post", back_populates=("posts.id"))
    author: Mapped["User"] = relationship("User", back_populates="comments")

    content: Mapped[str] = mapped_column(String(2500))
