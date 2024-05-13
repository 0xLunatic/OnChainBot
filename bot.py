import sys
import os
import json
import time
import requests
import random
from urllib.parse import unquote
from telethon import TelegramClient, sync, events
from telethon.tl.functions.messages import RequestWebViewRequest
from telethon.errors import SessionPasswordNeededError
from phonenumbers import is_valid_number as valid_number, parse as pp

from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

merah = "\033[91m"
putih = "\033[97m"
hijau = "\033[92m"
biru = "\033[94m"
reset = "\033[0m"

peer = "onchaincoin_bot"

class OnchainBot:
    def __init__(self):
        self.tg_data = None
        self.bearer = None
        self.peer = "onchaincoin_bot"
        self.api_id = api_id
        self.api_hash = api_hash

    def log(self, message):
        print(f"{biru}[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}{reset}")

    def countdown(self, t):
        while t:
            print(f"waiting for {t} seconds ", end="\r")
            t -= 1
            time.sleep(1)
        print(" " * 30, end="\r")

    def login(self, phone):
        session_folder = "session"

        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        if not valid_number(pp(phone)):
            self.log(f"{merah}phone number invalid !")
            sys.exit()

        client = TelegramClient(
            f"{session_folder}/{phone}", api_id=api_id, api_hash=api_hash
        )
        client.connect()
        if not client.is_user_authorized():
            try:
                client.send_code_request(phone)
                code = input(f"{putih}input login code : ")
                client.sign_in(phone=phone, code=code)
            except SessionPasswordNeededError:
                pw2fa = input(f"{putih}input password 2fa : ")
                client.sign_in(phone=phone, password=pw2fa)

        me = client.get_me()
        first_name = me.first_name
        last_name = me.last_name
        username = me.username
        self.log(f"{putih}Login as {hijau}{first_name} {last_name}")
        res = client(
            RequestWebViewRequest(
                peer=self.peer,
                bot=self.peer,
                platform="Android",
                url="https://db4.onchaincoin.io/",
                from_bot_menu=False,
            )
        )
        self.tg_data = unquote(res.url.split("#tgWebAppData=")[1]).split(
            "&tgWebAppVersion="
        )[0]
        return self.tg_data

    def get_info(self):
        _url = "https://db4.onchaincoin.io/api/info"
        _headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.5",
            "authorization": f"Bearer {self.bearer}",
            "referer": "https://db4.onchaincoin.io/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "te": "trailers",
            "content-length": "0",
        }
        res = requests.get(_url, headers=_headers, timeout=100)
        if res.status_code != 200:
            if "Invalid token" in res.text:
                return "need_reauth"

        data = res.json()["user"]
        self.log(f"{hijau}full name : {putih}:{data.get('fullName')}")
        self.log(f"{putih}total coins : {hijau}{data.get('coins')}")
        self.log(f"{putih}total clicks : {hijau}{data.get('clicks')}")
        self.log(f"{putih}total energy : {hijau}{data.get('energy')}")
        print("~" * 50)

    def on_login(self):
        _url = "https://db4.onchaincoin.io/api/validate"
        _data = {"hash": self.tg_data}
        _headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.5",
            "content-type": "application/json",
            "content-length": str(len(json.dumps(_data))),
            "origin": "https://db4.onchaincoin.io",
            "referer": "https://db4.onchaincoin.io/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "te": "trailers",
        }
        res = requests.post(_url, json=_data, headers=_headers, timeout=100)
        if res.status_code != 200 or not res.json().get("success"):
            sys.exit()

        self.bearer = res.json()["token"]
        return True

    def click(self):
        url = "https://db4.onchaincoin.io/api/klick/myself/click"
        _headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.5",
            "content-type": "application/json",
            "authorization": f"Bearer {self.bearer}",
            "content-length": "12",
            "origin": "https://db4.onchaincoin.io",
            "referer": "https://db4.onchaincoin.io/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "te": "trailers",
        }
        while True:
            try:
                click = random.randint(50, 150)
                _data = {"clicks": click}
                res = requests.post(url, json=_data, headers=_headers, timeout=100)

                if res.status_code != 200:
                    if "Invalid token" in res.text:
                        self.on_login()
                        continue

                if "error" in res.text:
                    self.countdown(self.sleep)
                    continue

                data = res.json()
                self.log(f"{hijau}click : {putih}{click}")
                self.log(f"{hijau}total clicks : {putih}{data.get('clicks')}")
                self.log(f"{hijau}total coins : {putih}{data.get('coins')}")
                self.log(f"{hijau}remaining energy : {putih}{data.get('energy')}")

                if click >= 1 and os.getenv("DISCORD_WEBHOOK"):
                    # Notify via Discord webhook
                    self.notify_discord(data)

                if int(data.get("energy", 0)) < int(self.min_energy):
                    self.countdown(self.sleep)
                    continue

                print("~" * 50)
                self.countdown(self.interval)
                continue

            except (requests.exceptions.RequestException, KeyboardInterrupt):
                sys.exit()

    def notify_discord(self, data):
        jakarta_timezone = pytz.timezone('Asia/Jakarta')
        now_jakarta = datetime.now(jakarta_timezone)
        formatted_date_time = now_jakarta.strftime("%d/%m/%Y %H:%M:%S")

        webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK"))
        embed = DiscordEmbed(title="Successfully Tapped!",
                             description=f"**Balance:** {data.get('coins')}\n **Taps:** +*{data.get('clicks')}*\n\n **Total Taps:** {data.get('clicks')}\n\n **DATE :** {formatted_date_time}",
                             color="03b2f8")
        webhook.add_embed(embed)
        webhook.execute()

    def main(self):
        banner = f"""
    {hijau}Auto tap-tap @onchaincoin_bot
    
    {biru}By t.me/rmndkyl
    github : @rmndkyl
    Recoded by : @0xLunatic{reset}
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        print(banner) 

        if not os.path.exists("tg_data"):
            print(f"{putih}example input : +628169696969")
            phone = input(f"{hijau}input telegram phone number : {putih}")
            print()
            data = self.login(phone)
            open("tg_data", "w").write(data)

        tg_data = open("tg_data", "r").read()
        self.tg_data = tg_data
        read_config = open("config.json", "r").read()
        load_config = json.loads(read_config)
        self.interval = load_config["interval"]
        self.sleep = load_config["sleep"]
        self.min_energy = load_config["min_energy"]
        self.on_login()
        self.get_info()
        self.click()


if __name__ == "__main__":
    try:
        app = OnchainBot()
        app.main()
    except KeyboardInterrupt:
        sys.exit()
