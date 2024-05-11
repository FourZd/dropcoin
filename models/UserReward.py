from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String, BigInteger
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class UserReward(EntityMeta):
    __tablename__ = "user_rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    reward_type_id = Column(Integer, ForeignKey('available_rewards.id')) # TODO make Enum? 
    timestamp = Column(DateTime(timezone=True))
    ref_code = Column(String, nullable=True)
    user = relationship("User", back_populates="rewards")
    reward_type = relationship("AvailableReward", back_populates="user_rewards")
    