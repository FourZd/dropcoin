from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String, BigInteger, Numeric
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class UserTransaction(EntityMeta):
    __tablename__ = "user_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    profit = Column(Numeric)
    timestamp = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="transactions")