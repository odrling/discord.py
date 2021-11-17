from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from operator import attrgetter
from typing import TYPE_CHECKING, Any

from .enums import ChannelType
from .user import User

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.guild_event import GuildEvent as GuildEventPayload


class PrivacyLevel(Enum):
    PUBLIC = 1
    GUILD_ONLY = 2


class GuildEventStatus(Enum):
    SCHEDULED = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELED = 4


class GuildEventEntityType(Enum):
    NONE = 0
    STAGE_INSTANCE = 1
    VOICE = 2
    EXTERNAL = 3


@dataclass
class GuildEventEntityMetadata:
    speaker_ids: list[int] | None = None
    location: str | None = None

    @classmethod
    def from_payload(cls, data: dict[str, Any] | None):
        if data is None:
            return cls()

        if 'speaker_ids' in data:
            data['speaker_ids'] = [int(id) for id in data['speaker_ids']]

        return cls(**data)


class GuildEvent:

    def __init__(self, *, state: ConnectionState, data: GuildEventPayload):
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, data: GuildEventPayload):
        self.id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])

        self.channel_id: int | None = int(
            data['channel_id']) if data['channel_id'] is not None else None

        self.creator_id: int | None = int(
            data['creator_id']) if 'creator_id' in data else None

        self.name: str = data['name']
        self.description: str | None = data.get('description')
        self.image: str | None = data['image']

        self.scheduled_start_time: datetime = datetime.fromisoformat(
            data['scheduled_start_time'])
        self.scheduled_end_time: str | None = datetime.fromisoformat(
            data['scheduled_end_time']
        ) if data['scheduled_end_time'] is not None else None

        self.privacy_level: PrivacyLevel = PrivacyLevel(
            int(data['privacy_level']))

        self.status: GuildEventStatus = GuildEventStatus(int(data['status']))

        self.entity_type: GuildEventEntityType = GuildEventEntityType(
            int(data['entity_type']))
        self.entity_id: int | None = int(
            data['entity_id']) if data['entity_id'] is not None else None
        self.entity_metadata: GuildEventEntityMetadata = GuildEventEntityMetadata.from_payload(
            data['entity_metadata'])

        self.user_count: int | None = int(
            data['user_count']) if 'user_count' in data else None

    async def edit(
            self,
            name: str = ...,
            entity_type: GuildEventEntityType = ...,
            privacy_level: PrivacyLevel = ...,
            status: GuildEventStatus = ...,
            scheduled_start_time: datetime = ...,
            scheduled_end_time: datetime | None = ...,
            description: str | None = ...,
            channel_id: int | None = ...,
            entity_metadata: GuildEventEntityMetadata | None = ...
    ) -> 'GuildEvent':
        """
        Modify a guild scheduled event.
        Returns the modified guild scheduled event object on success.
        """
        data: dict[str, Any] = {}

        if name != ...:
            data['name'] = name
        if entity_type != ...:
            data['entity_type'] = entity_type.value
        if privacy_level != ...:
            data['privacy_level'] = privacy_level.value
        if status != ...:
            data['status'] = status.value
        if scheduled_start_time != ...:
            data['scheduled_start_time'] = scheduled_start_time.isoformat()
        if scheduled_end_time != ...:
            data['scheduled_end_time'] = scheduled_end_time.isoformat()
        if description != ...:
            data['description'] = description
        if channel_id != ...:
            data['channel_id'] = channel_id
        if entity_metadata != ...:
            data['entity_metadata'] = asdict(entity_metadata)

        result = await self._state.http.edit_guild_event(
            self.guild_id, self.id, data)
        return type(self)(state=self._state, data=result)

    async def delete(self):
        """
        Delete a guild scheduled event. Returns a 204 on success.
        """
        await self._state.http.delete_guild_event(self.guild_id, self.id)

    async def get_users(self,
                        limit: int = 100,
                        with_member: bool = False) -> list[User]:
        """
        Get a list of users RSVP'd to the guild scheduled event.
        Returns a list of user objects on success with an optional guild_member
        property for each user if with_member query parameter is passed in.
        """
        result = await self._state.http.get_guild_event_users(
            self.guild_id, self.id, limit=limit, with_member=with_member)
        return [User(state=self._state, data=user) for user in result['users']]

    async def create_link(self, **kwargs) -> str:
        """
        Guild event invite link
        """
        if self.channel_id is not None:
            channel = self._state.get_channel(self.channel_id)
            if channel is None:
                channel = await self._state.http.get_channel(self.channel_id)

        else:
            guild = self._state._get_guild(self.guild_id)
            if guild is None:
                guild = await self._state.http.get_guild(self.guild_id)

            if guild.system_channel is not None:
                channel = guild.system_channel
            else:
                g_chans = sorted(guild.channels, key=attrgetter('position'))
                for c in g_chans:
                    if c.type == ChannelType.text:
                        channel = c
                        break

        invite = await channel.create_invite(**kwargs)
        return f"{invite.url}?event={self.id}"
