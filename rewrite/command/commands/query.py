from utils import magic

def run(type="user", target="default"):
    if target == "default":
        target = magic.get_from_first_parent("client")
        print(target)
        print(target.user.id)