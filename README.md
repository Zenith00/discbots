# Discbots


Development Repository for my Discord bots

### M3R-CY

All-purpose administration bot

###### Active commands
| Command             | Parameters         | Description                                                                           |
|---------------------|--------------------|---------------------------------------------------------------------------------------|
| ui/userinfo         | [User]             | Generates a userinfo embed for [User]                                                 |
| ping                |                    | Evaluates functional ping from MERCY to server                                        |
|                     |                    |                                                                                       |
| query user dumpinfo | [User]             | Dumps a history of recorded names, nicknames, avatars, and server movement for [User] |
| query role list     | ?Server            | Lists roles in [Server], defaults to server where command used                        |
| query role members  | Role               | Lists members of [Role]                                                               |
| query emoji         | Emoji              | Dumps server of origin, ID, and size of [Emoji]                                       |
| query channel       | Channel            | Dumps channel settings and permissions of [Channel]                                   |
| tag set             | Tag Expansion+     | Starts tagging process for an expansion of a given tag                                |
| tag list            |                    | Lists set tags                                                                        |
| tag unset           | Tag                | Unsets tag                                                                            |
| logs                | see below          | Generates and returns logs via hastebin                                               |
|                     |                    |                                                                                       |
| purge               | Channel Count      | Purges [Count] messages from [Channel]                                                |
| fixchannels         |                    | Repairs channel names to backup                                                       |
| reactions           | Message            | Parses and dumps reactions on [Message]                                               |
| deletereacts        | Message            | Removes reactions from [Message]                                                      |
| serverlog           |                    | Toggles server logging backup function                                                |
| joinwarn            |                    | Toggles join warning                                                                  |
| watcher             |                    | Parses and multibans watcher alert                                                    |
| filter add          | Regex              | Adds [Regex] to action filter                                                         |
| filter remove       | Regex              | Removes [Regex] from action filter                                                    |
| jukeskip            | User SkipTarget    | Interfaces with LUC-10 to skip a song titled [SkipTarget] from [User]                 |
| raw                 | Message            | Returns raw content of [Message]                                                      |
| forceban            | User               | Forcebans [User] from server                                                          |
| moveafk             | User               | Forcibly moves user to AFK channel                                                    |
| join                | User               | Generates a join link to [User]'s active voice channel                                |
| find                | Username           | Fuzzy searches [Username] among all current members                                   |
| findall             | Username           | Fuzzy searches [Username] among all stored members and history                        |
| findban             | Username           | Fuzzy searches [Username] among all banned members                                    |
| mute                | User Duration      | Applies the Muted role to [User] for [Duration]. Macro for temprole                   |
| temprole add        | Role User Duration | Applies [Role] to [User] for [Duration]                                               |
| temprole remove     | Role User          | Removes [Role] from [User], cancels temprole                                          |
| temprole tick       |                    | Forcibly resets and reapplies temproles to users                                      |
| temprole list       |                    | Lists currently active temproles                                                      |
| channelmute         | [Channel]          | Mutes all standard members in [Channel]                                               |
| massban             | Start End          | Mass forcebans member joins between Start and End                                     |
| remindme            | Duration Message+  | Pings user after [Duration] with [Message]                                            |

###### Passive functions

* Computes message heat for users, provides warning capabilities from excessive message heat
* Logs all messages, name changes, server movement, avatar changes
* Automatically deletes non-moderator messages that contain arbitrary regex matches
* Provides command wrappers and correctors for other bots



### Logbot

* [prefix]register to restart the registration process
* [prefix]toggle <logname> to toggle a log on or off
* [prefix]setprefix to change the bot's prefix
* [prefix]oauth to get an invite link
* [prefix]info to see current log positions


