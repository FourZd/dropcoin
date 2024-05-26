from pydantic import BaseModel

class CollectPointsRequest(BaseModel):
    mission_id: int