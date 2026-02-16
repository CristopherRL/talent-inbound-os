"""Shared value objects for the Talent Inbound OS domain."""

from typing import Annotated

from pydantic import Field

Email = Annotated[
    str, Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
]

NonEmptyStr = Annotated[str, Field(min_length=1)]

MatchScore = Annotated[int, Field(ge=0, le=100)]
