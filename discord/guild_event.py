from __future__ import annotations

from datetime import datetime
from operator import attrgetter
from typing import TYPE_CHECKING, Any

from .enums import (ChannelType, GuildEventEntityType, GuildEventPrivacyLevel,
                    GuildEventStatus)
from .member import Member
from .user import User

if TYPE_CHECKING:
    from .channel import VocalGuildChannel
    from .guild import Guild
    from .state import ConnectionState
    from .types.guild_event import GuildEvent as GuildEventPayload
    from .types.guild_event import \
        GuildEventEntityMetadata as GuildEventEntityMetadataPayload


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
            data['creator_id']) if data['creator_id'] is not None else None

        self.name: str = data['name']
        self.description: str | None = data.get('description')

        self.scheduled_start_time: datetime = datetime.fromisoformat(
            data['scheduled_start_time'])
        self.scheduled_end_time: str | None = datetime.fromisoformat(
            data['scheduled_end_time']
        ) if data['scheduled_end_time'] is not None else None

        self.privacy_level: GuildEventPrivacyLevel = GuildEventPrivacyLevel(
            int(data['privacy_level']))

        self.status: GuildEventStatus = GuildEventStatus(int(data['status']))

        self.entity_type: GuildEventEntityType = GuildEventEntityType(
            int(data['entity_type']))
        self.entity_id: int | None = int(
            data['entity_id']) if data['entity_id'] is not None else None

        self._unroll_metadata(data['entity_metadata'])

        self.creator: User | None = User(
            state=self._state,
            data=data['creator']) if 'creator' in data else None

        self.user_count: int | None = int(
            data['user_count']) if 'user_count' in data else None

    def _unroll_metadata(self, data: GuildEventEntityMetadataPayload | None):
        if data is None:
            data = {}
        self.location: str | None = data.get('location')

    @property
    def guild(self) -> Guild | None:
        return self._state._get_guild(self.guild_id)

    @property
    def channel(self) -> VocalGuildChannel | None:
        return self._state.get_channel(self.channel_id)

    async def edit(self,
                   name: str = ...,
                   entity_type: GuildEventEntityType = ...,
                   status: GuildEventStatus = ...,
                   scheduled_start_time: datetime = ...,
                   scheduled_end_time: datetime | None = ...,
                   description: str | None = ...,
                   channel_id: int | None = ...,
                   location: str | None = ...,
                   privacy_level: GuildEventPrivacyLevel = ...) -> 'GuildEvent':
        """
        Modify a guild scheduled event.
        Returns the modified guild scheduled event object on success.
        To start or end an event, use this endpoint to modify the event's status field.
        """
        data: dict[str, Any] = {}

        if name != ...:
            data['name'] = name
        if entity_type != ...:
            data['entity_type'] = entity_type.value
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
        if location != ...:
            data['entity_metadata'] = {'location': location}
        if privacy_level != ...:
            data['privacy_level'] = privacy_level.value

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
                        with_member: bool = False,
                        before: int = None,
                        after: int = None) -> list[User | Member]:
        """
        Get a list of guild scheduled event users subscribed to a guild scheduled event.
        Returns a list of guild scheduled event user objects on success.
        Guild member data, if it exists, is included if the with_member query parameter is set.
        """
        result = await self._state.http.get_guild_event_users(
            self.guild_id,
            self.id,
            limit=limit,
            with_member=with_member,
            before=before,
            after=after)
        users = []
        for user in result:
            if (member_data := user.get('member')) is not None:
                member_data['user'] = user['user']
                guild = self._state._get_guild(self.guild_id)
                users.append(
                    Member(data=member_data, guild=guild, state=self._state))
            else:
                users.append(User(state=self._state, data=user['user']))
        return users

    async def create_link(self, **kwargs) -> str:
        """
        Guild event invite link
        """
        if self.channel is not None:
            channel = self.channel
        else:
            guild = self._state._get_guild(self.guild_id)
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
