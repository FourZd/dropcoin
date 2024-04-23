from pydantic import BaseModel

class CollectPointsRequest(BaseModel):
    mission_id: int
    additional_parameter: str = None