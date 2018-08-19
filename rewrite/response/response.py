import asyncio
import datetime
import discord


class ResponseRouter:
    def __init__(self, client):
        self.client = client
        self.responses = []
        pass

    def create_response(self, **kwargs):
        res = Response(**kwargs)
        self.responses.append(res)

    def add_response(self, response):
        self.responses.append(response)

class Response:
    def __init__(self,
                 target: discord.TextChannel,
                 text: str = "",
                 file = None,
                 embed: discord.Embed = None,
                 expire_datetime: datetime.datetime = None):
        if expire_datetime:
            expire_datetime = (datetime.datetime.now(tz=datetime.timezone.utc) - expire_datetime).seconds
        self.message = target.send(content=text, embed=embed, file=file, files=None, delete_after=expire_datetime)
