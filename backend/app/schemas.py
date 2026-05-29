from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoardCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    details: str


class BoardColumn(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    title: str
    card_ids: list[str] = Field(alias="cardIds")


class BoardState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[BoardColumn]
    cards: dict[str, BoardCard]

    @model_validator(mode="after")
    def validate_card_references(self) -> "BoardState":
        missing = [
            card_id
            for column in self.columns
            for card_id in column.card_ids
            if card_id not in self.cards
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Column references missing card ids: {joined}")
        return self


class AIKanbanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    assistant_message: str = Field(alias="assistantMessage")
    apply_board_update: bool = Field(alias="applyBoardUpdate")
    updated_board: BoardState | None = Field(default=None, alias="updatedBoard")

    @model_validator(mode="after")
    def validate_update_pairing(self) -> "AIKanbanResponse":
        if self.apply_board_update and self.updated_board is None:
            raise ValueError("updatedBoard is required when applyBoardUpdate is true")
        if not self.apply_board_update and self.updated_board is not None:
            raise ValueError("updatedBoard must be null when applyBoardUpdate is false")
        return self
