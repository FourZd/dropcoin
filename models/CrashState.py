from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Numeric, String
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class CrashState(EntityMeta):
    __tablename__ = 'game_state'

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_game_hash = Column(String)
    current_result = Column(Numeric)
    betting_close_time = Column(DateTime(timezone=True), nullable=False)
    last_game_hash = Column(String)
    last_game_result = Column(Numeric)
    next_game_time = Column(DateTime(timezone=True), nullable=False)
    
