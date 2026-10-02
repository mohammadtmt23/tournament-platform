from pydantic import BaseModel, Field


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    game: str = Field(min_length=1, max_length=100)


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ResultIn(BaseModel):
    winner_id: int
