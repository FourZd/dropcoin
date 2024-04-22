from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class AvailableReward(EntityMeta):
    __tablename__ = "available_rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    reward = Column(Integer)
    description = Column(String)

    user_rewards = relationship("UserReward", back_populates="reward_type", uselist=True)