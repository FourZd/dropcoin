from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, BigInteger, Numeric
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship

class Farming(EntityMeta):
    __tablename__ = "farmings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    reward = Column(Numeric)

    user = relationship("User", back_populates="farmings")