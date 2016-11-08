messInfo = {"userid": "userid",
    "content"           : "messageContent",
    "length"            : "messageLength",
    "date"              : "mess.timestamp.isoformat(" ")",
    "mentioned_users"   : "mentioned_users",
    "mentioned_channels": "mentioned_channels",
    "mentioned_roles"   : "mentioned_roles",
}


mongo_string = '''{{
        "useridA":"{userid}",
        "contentA":"{content}",
        "lengthA":"{length}",
        "dateA":"{date}",
        "mentioned_usersA":"{mentioned_users}",
        "mentioned_rolesA":"{mentioned_roles}",
    }}
'''.format(userid=messInfo["userid"], content=messInfo["content"], length=messInfo["length"],
           date=messInfo["date"], mentioned_users=messInfo["mentioned_users"],
           mentioned_channels=messInfo["mentioned_channels"],
           mentioned_roles="Asdf")
print(mongo_string)


print(str(eval(mongo_string)))