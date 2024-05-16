from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Numeric
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship
from models.Farming import Farming

class User(EntityMeta):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True))
    referrer_id = Column(String, ForeignKey('users.id'))
    wallet_address = Column(String)

    bets = relationship("CrashBet", back_populates="user")
    rewards = relationship("UserReward", back_populates="user")
    referrer = relationship("User", back_populates="referrals", remote_side=[id])
    referrals = relationship("User", back_populates="referrer")
    twitter_posts = relationship("TwitterPost", back_populates="user")
    transactions = relationship("UserTransaction", back_populates="user")
    farmings = relationship("Farming", back_populates="user")
    