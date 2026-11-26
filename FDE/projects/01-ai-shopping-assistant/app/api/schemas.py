from pydantic import BaseModel


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int
