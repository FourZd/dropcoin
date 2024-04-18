from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class CrashState(EntityMeta):
    __tablename__ = 'game_state'

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_game_hash_id = Column(Integer, ForeignKey('crash_hashes.id'))
    last_game_hash_id = Column(Integer, ForeignKey('crash_hashes.id'), nullable=True)
    last_game_result = Column(Float)
    next_game_time = Column(DateTime, nullable=False)
    betting_close_time = Column(DateTime, nullable=False)

    current_game_hash = relationship("CrashHash", foreign_keys=[current_game_hash_id], back_populates="current_game_states")
    last_game_hash = relationship("CrashHash", foreign_keys=[last_game_hash_id], back_populates="last_game_states")
