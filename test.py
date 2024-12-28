import asyncio
import sys

sys.path.append("c:\\development\\ericfoss\\python-gamedig")

from gamedig import GameDig


async def main():
    # gd = GameDig("valheim", "192.168.1.65")
    gd = GameDig("minecraft", "10.152.183.26")
    print(await gd.query())


if __name__ == "__main__":
    asyncio.run(main())
