from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Numeric, String
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class GameHistory(EntityMeta):
    __tablename__ = 'game_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_hash = Column(String)
    result = Column(Numeric)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)