from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship

class User(EntityMeta):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True))
    referrer_id = Column(BigInteger, ForeignKey('users.id'))
    wallet_address = Column(String)

    bets = relationship("CrashBet", back_populates="user")
    rewards = relationship("UserReward", back_populates="user")
    referrer = relationship("User", back_populates="referrals", remote_side=[id])
    referrals = relationship("User", back_populates="referrer")
    twitter_posts = relationship("TwitterPost", back_populates="user")