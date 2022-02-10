from __future__ import annotations

import copy
import inspect
import typing

from discord.enums import Enum
from discord import User, Mentionable, Role, ChannelType, Interaction
from discord.abc import GuildChannel

from dataclasses import dataclass

__all__ = ['ApplicationCommand',
           'ApplicationCommandField',
           'slash_command']

_pre_registration_commands = {}
_registered_global_commands = {}
_registered_guild_commands = {}


#  ENUMS


class ApplicationCommandOptionType(Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 8
    NUMBER = 10


class ApplicationCommandType(Enum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


class ApplicationCommandPermissionType(Enum):
    ROLE = 1
    USER = 2


# DATACLASSES

@dataclass
class ApplicationCommandPermission:
    id: int
    type: ApplicationCommandPermissionType
    permission: bool


@dataclass
class ApplicationCommandInteractionDataOption:
    name: str
    type: int
    value: ApplicationCommandOptionType | None = None
    options: typing.List[ApplicationCommandInteractionDataOption] | None = None
    focused: bool = False

    def __repr__(self):
        data = {
            "name": self.name,
            "type": self.type,
            "focused": self.focused
        }

        if self.value is not None:
            data["value"] = self.value.value

        if self.options is not None:
            data["options"] = []
            for option in self.options:
                data["options"].append(option)

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandInteractionDataOption):
            return False
        if (self.name != other.name or
                self.type != other.type or
                self.value.value != other.value.value or
                self.options != other.options or
                self.focused != other.focused):
            return False
        return True


@dataclass
class ApplicationCommandOptionChoice:
    name: str
    value: typing.Union[str | int | float]

    def __repr__(self):
        data = {
            "name": self.name,
            "value": self.value
        }
        return data

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandOptionChoice):
            return False
        if self.name != other.name or self.value != other.value:
            return False
        return True

    def __ne__(self, other):
        return not self == other


@dataclass
class ApplicationCommandOption:
    type: ApplicationCommandOptionType
    name: str
    description: str = None
    required: bool = False
    choices: typing.List[ApplicationCommandOptionChoice] | None = None
    options: typing.List[ApplicationCommandOption] | None = None
    channel_types: typing.List[ChannelType] | None = None
    min_value: int | None = None
    max_value: int | None = None
    autocomplete: bool = False
    default_value: typing.Any = None

    def __post_init__(self):
        if self.type is not None and isinstance(self.type, int):
            self.type = ApplicationCommandOptionType(self.type)
        if self.choices is not None and any(not isinstance(x, ApplicationCommandOptionChoice) for x in self.choices):
            buffer_choices = copy.copy(self.choices)
            self.choices = []
            for buffer_choice in buffer_choices:
                self.choices.append(ApplicationCommandOptionChoice(**buffer_choice))
        if self.options is not None and any(not isinstance(x, ApplicationCommandOption) for x in self.options):
            buffer_options = copy.copy(self.options)
            self.options = []
            for buffer_option in buffer_options:
                self.options.append(ApplicationCommandOption(**buffer_option))

    def value(self, interaction: Interaction, uncoded):
        if self.type == ApplicationCommandOptionType.STRING:
            return str(uncoded)
        elif self.type == ApplicationCommandOptionType.NUMBER:
            return float(uncoded)
        elif self.type == ApplicationCommandOptionType.BOOLEAN:
            return bool(uncoded)
        elif self.type == ApplicationCommandOptionType.INTEGER:
            return int(uncoded)
        elif self.type == ApplicationCommandOptionType.USER:
            return interaction.guild.get_member(int(uncoded))
        elif self.type == ApplicationCommandOptionType.CHANNEL:
            return interaction.guild.get_channel(int(uncoded))
        elif self.type == ApplicationCommandOptionType.ROLE:
            return interaction.guild.get_role(int(uncoded))
        elif self.type == ApplicationCommandOptionType.MENTIONABLE:
            return None
        return uncoded  # We don't touch the value if no types match but it should never happen

    def __repr__(self):
        data = {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "required": self.required,
            "autocomplete": self.autocomplete
        }
        if self.choices is not None:
            data["choices"] = []
            for choice in self.choices:
                data["choices"].append(choice.__repr__())

        if self.options is not None:
            data["options"] = []
            for option in self.options:
                data["options"].append(option.__repr__())

        if self.channel_types is not None:
            data["channel_types"] = []
            for channel_type in self.channel_types:
                data["channel_types"].append(channel_type.value)

        if self.min_value is not None:
            data["min_value"] = self.min_value

        if self.max_value is not None:
            data["max_value"] = self.max_value

        return data

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandOption):
            return False
        if (self.type.value != other.type.value or
                self.name != other.name or
                self.description != other.description or
                self.autocomplete != other.autocomplete or
                self.max_value != other.max_value or
                self.min_value != other.min_value or
                self.channel_types != other.channel_types or
                self.required != other.required or
                self.options != other.options or
                self.choices != other.choices):
            return False
        return True

    def __ne__(self, other):
        return not self == other

    @classmethod
    def from_payload(cls, data: dict[str, typing.Any] | None):
        if data is None:
            return cls()
        return cls(**data)


class ApplicationCommand:

    def __init__(self,
                 name: str,
                 description: str,
                 callback: typing.Any | None = None,
                 id: int | None = None,
                 application_id: int | None = None,
                 version: int | None = None,
                 type: int | ApplicationCommandType = ApplicationCommandType.CHAT_INPUT,
                 guild_id: str = None,
                 options: typing.List[ApplicationCommandOption] = None,
                 default_permission: bool = True,
                 default_member_permissions: bool | None = None,
                 dm_permission: bool | None = None,
                 is_global: bool = False,
                 ephemeral: bool = True,
                 cog=None):
        self.callback: typing.Any | None = callback
        self.id: int | None = id
        if isinstance(type, int):
            self.type: ApplicationCommandType = ApplicationCommandType(type)
        else:
            self.type: ApplicationCommandType = type
        self.application_id: int | None = application_id
        self.guild_id: str | None = guild_id
        self.name: str = name
        self.description: str = description
        # options est une list de ApplicationCommandOption
        if options is None or any(isinstance(x, ApplicationCommandOption) for x in options):
            self.options: typing.List[ApplicationCommandOption] | None = options
        else:
            self.options: typing.List[ApplicationCommandOption] = []
            for option in options:
                self.options.append(ApplicationCommandOption.from_payload(option))

        self.default_permission: bool = default_permission
        self.default_member_permissions: bool | None = default_member_permissions
        self.dm_permission: bool | None = dm_permission
        self.version: int = version
        self.is_global = is_global
        self.ephemeral = ephemeral
        self.cog = cog

    @classmethod
    def from_payload(cls, data: dict[str, typing.Any] | None):
        if data is None:
            return cls()
        return cls(**data)

    def generate_options_value(self, interaction: Interaction) -> dict:
        options_and_value = {}
        received_values = {}
        data = interaction.data
        if "options" in data:
            for option in data["options"]:
                received_values[option["name"]] = option["value"]
        if self.options is not None:
            for option in self.options:
                options_and_value[option.name] = option.default_value
                if option.name in received_values:
                    options_and_value[option.name] = option.value(interaction, received_values[option.name])
        return options_and_value

    def __copy__(self):
        return ApplicationCommand(type=self.type,
                                  name=self.name,
                                  guild_id=self.guild_id,
                                  description=self.description,
                                  callback=self.callback,
                                  options=self.options,
                                  is_global=self.is_global)

    def __repr__(self):
        data = {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "default_permission": self.default_permission
        }
        if self.id is not None:
            data["id"] = self.id
        if self.application_id is not None:
            data["application_id"] = self.application_id
        if self.version is not None:
            data["version"] = self.version
        if self.guild_id is not None:
            data["guild_id"] = int(self.guild_id)
        if self.options is not None:
            data["options"] = []
            for option in self.options:
                data["options"].append(option.__repr__())
        return data

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommand):
            return False
        if (self.type.value != other.type.value or
                self.name != other.name or
                self.description != other.description or
                self.guild_id != other.guild_id or
                self.default_permission != other.default_permission or
                self.default_member_permissions != other.default_member_permissions or
                self.dm_permission != other.dm_permission or
                self.options != other.options):
            return False
        return True

    def __ne__(self, other):
        return not self == other


class ApplicationCommandField:

    def __init__(self,
                 description: str = "No description yet",
                 required: bool = False,
                 values: typing.Dict[str, str | int | float] | None = None,
                 default_value: str | int | float | None = None,
                 min_value: int | float | None = None,
                 max_value: int | float | None = None):
        self.description = description
        self.required = required
        self.values = values
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value


def slash_command(name: str | None = None,
                  description: str | None = None,
                  is_global: bool = False,
                  ephemeral: bool = True):
    """
    Create an Application Command for discord
    :param name: The name of command
    :param description: The description of the command
    :param is_global: If set to True, the command will be deployed on every guild servers but won't be a global command
    :return: An instance of the Application Command
    """
    def slash_command_decorator(callback):
        if description:
            command_description = description
        else:
            command_description = 'No description yet'
        if not name:
            command_name = callback.__name__
        else:
            command_name = name

        signature = inspect.signature(callback)
        parameters = signature.parameters.copy()
        options = None
        if len(parameters) > 0:
            for parameter_name, parameter in parameters.items():
                command_field: ApplicationCommandField | None = parameter.default
                required = False
                min_value = None
                max_value = None
                option_description = "No description yet."
                choices = None
                default_value = None
                if command_field is not inspect._empty:
                    required = command_field.required
                    option_description = command_field.description
                    default_value = command_field.default_value
                if issubclass(parameter.annotation, str):
                    current_type = ApplicationCommandOptionType.STRING
                    if command_field is not inspect._empty and command_field.values is not None:
                        choices = [ApplicationCommandOptionChoice(n, v) for n, v in command_field.values.items()]
                elif issubclass(parameter.annotation, int):
                    current_type = ApplicationCommandOptionType.INTEGER
                    if command_field is not inspect._empty:
                        min_value = command_field.min_value
                        max_value = command_field.max_value
                        if command_field.values is not None:
                            choices = [ApplicationCommandOptionChoice(n, v) for n, v in command_field.values.items()]
                elif issubclass(parameter.annotation, float):
                    current_type = ApplicationCommandOptionType.NUMBER
                    if command_field is not inspect._empty:
                        min_value = command_field.min_value
                        max_value = command_field.max_value
                        if command_field.values is not None:
                            choices = [ApplicationCommandOptionChoice(n, v) for n, v in command_field.values.items()]
                elif issubclass(parameter.annotation, bool):
                    current_type = ApplicationCommandOptionType.BOOLEAN
                elif issubclass(parameter.annotation, User):
                    current_type = ApplicationCommandOptionType.USER
                elif issubclass(parameter.annotation, GuildChannel):
                    current_type = ApplicationCommandOptionType.CHANNEL
                elif issubclass(parameter.annotation, Role):
                    current_type = ApplicationCommandOptionType.ROLE
                elif issubclass(parameter.annotation, Mentionable):
                    current_type = ApplicationCommandOptionType.MENTIONABLE
                else:
                    continue
                if options is None:
                    options = []
                options.append(ApplicationCommandOption(type=current_type,
                                                        name=parameter_name,
                                                        description=option_description,
                                                        choices=choices,
                                                        required=required,
                                                        min_value=min_value,
                                                        max_value=max_value,
                                                        default_value=default_value))

        command = ApplicationCommand(type=ApplicationCommandType.CHAT_INPUT,
                                     name=command_name,
                                     description=command_description,
                                     callback=callback,
                                     options=options,
                                     is_global=is_global,
                                     ephemeral=ephemeral)
        return command

    return slash_command_decorator
