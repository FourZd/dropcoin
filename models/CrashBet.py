from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship

class CrashBet(EntityMeta):
    __tablename__ = "crash_bets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    amount = Column(Float)
    time = Column(DateTime(timezone=True))
    game_id = Column(Integer, ForeignKey('crash_hashes.id'))
    cash_out_multiplier = Column(Float, nullable=True)

    # Relationship to access user information from a bet
    user = relationship("User", back_populates="bets")
    game = relationship("CrashHash", foreign_keys=[game_id], back_populates="bets")





