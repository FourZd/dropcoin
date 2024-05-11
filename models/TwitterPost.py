from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship

class TwitterPost(EntityMeta):
    __tablename__ = "twitter_posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True))
    post_url = Column(String)
    post_type = Column(String)
    
    user = relationship("User", back_populates="twitter_posts")