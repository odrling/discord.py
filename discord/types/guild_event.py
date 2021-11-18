from __future__ import annotations

from typing import Literal, Optional, TypedDict

from .member import Member
from .snowflake import Snowflake, SnowflakeList
from .user import User

GuildEventPrivacyLevel = Literal[2]
GuildEventStatus = Literal[1, 2, 3, 4]
GuildEventEntityType = Literal[1, 2, 3]


class GuildEventEntityMetadata(TypedDict, total=False):
    location: str


class GuildEvent(TypedDict, total=False):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Optional[Snowflake]
    creator_id: Optional[Snowflake]
    name: str
    description: str
    scheduled_start_time: str
    scheduled_end_time: Optional[str]
    privacy_level: GuildEventPrivacyLevel
    status: GuildEventStatus
    entity_type: GuildEventEntityType
    entity_id: Optional[Snowflake]
    entity_metadata: Optional[GuildEventEntityMetadata]
    creator: User
    user_count: int


class GuildEventUser(TypedDict, total=False):
    guild_scheduled_event_id: Snowflake
    user: User
    member: Member
