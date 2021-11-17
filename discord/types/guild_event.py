from __future__ import annotations

from typing import Literal, Optional, TypedDict

from .channel import PrivacyLevel
from .snowflake import Snowflake, SnowflakeList
from .user import User

GuildEventStatus = Literal[1, 2, 3, 4]
GuildEventEntityType = Literal[0, 1, 2, 3]


class GuildEventEntityMetadata(TypedDict, total=False):
    speaker_ids: SnowflakeList
    location: str


class GuildEvent(TypedDict, total=False):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Optional[Snowflake]
    creator_id: Snowflake
    name: str
    description: str
    scheduled_start_time: str
    scheduled_end_time: Optional[str]
    privacy_level: PrivacyLevel
    status: GuildEventStatus
    entity_type: GuildEventEntityType
    entity_id: Optional[Snowflake]
    entity_metadata: Optional[GuildEventEntityMetadata]
    creator: User
    user_count: int


class GuildEventUsers(TypedDict):
    users: list[User]
