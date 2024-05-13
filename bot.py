import sys
import os
import json
import time
import requests
import random
import aiohttp
import asyncio
from urllib.parse import unquote
from phonenumbers import is_valid_number as valid_number, parse as pp
from colorama import *
from dotenv import load_dotenv

from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime
import pytz

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

init(autoreset=True)

merah = Fore.LIGHTRED_EX
putih = Fore.LIGHTWHITE_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL

peer = "onchaincoin_bot"


class OnchainBot:
    def __init__(self):
        self.tg_data = None
        self.bearer = None
        self.peer = "onchaincoin_bot"
        self.api_id = api_id
        self.api_hash = api_hash

    def log(self, message):
        year, mon, day, hour, minute, second, a, b, c = time.localtime()
        mon = str(mon).zfill(2)
        hour = str(hour).zfill(2)
        minute = str(minute).zfill(2)
        second = str(second).zfill(2)
        print(f"{biru}[{year}-{mon}-{day} {hour}:{minute}:{second}] {message}")

    def countdown(self, t):
        while t:
            menit, detik = divmod(t, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"waiting until {jam}:{menit}:{detik} ", flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    async def login(self, phone):
        session_folder = "session"

        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        if not valid_number(pp(phone)):
            self.log(f"{merah}phone number invalid !")
            sys.exit()

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://my.telegram.org/auth/send_password?phone={phone}") as response:
                if response.status != 200:
                    self.log("Failed to send code.")
                    return

                html = await response.text()
                self.log("Enter the code you received.")
                code = input("Code: ")
                async with session.get(f"https://my.telegram.org/auth/login?phone={phone}&password={code}") as login_response:
                    if login_response.status != 200:
                        self.log("Login failed.")
                        return

                    self.log("Successfully logged in.")
                    return

    def get_info(self):
        _url = "https://db4.onchaincoin.io/api/info"
        _headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.5",
            "authorization": f"Bearer {self.bearer}",
            "referer": "https://db4.onchaincoin.io/",
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            "te": "trailers",
            "content-length": "0",
        }
        res = requests.get(_url, headers=_headers, timeout=100)
        if res.status_code != 200:
            if "Invalid token" in res.text:
                return "need_reauth"

        name = res.json()["user"]["fullName"]
        energy = res.json()["user"]["energy"]
        max_energy = res.json()["user"]["maxEnergy"]
        league = res.json()["user"]["league"]
        clicks = res.json()["user"]["clicks"]
        coins = res.json()["user"]["coins"]
        self.log(f"{hijau}full name : {putih}:{name}")
        self.log(f"{putih}total coins : {hijau}{coins}")
        self.log(f"{putih}total clicks : {hijau}{clicks}")
        self.log(f"{putih}total energy : {hijau}{energy}")
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
        if res.status_code != 200:
            print(res.text)
            sys.exit()

        if res.json()["success"] is False:
            print(res.text)
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

                clicks = res.json()["clicks"]
                coins = res.json()["coins"]
                energy = res.json()["energy"]
                self.log(f"{hijau}click : {putih}{click}")
                self.log(f"{hijau}total clicks : {putih}{clicks}")
                self.log(f"{hijau}total coins : {putih}{coins}")
                self.log(f"{hijau}remaining energy : {putih}{energy}")
                if click >= 1:
                    if os.getenv("DISCORD_WEBHOOK"):
                        # Specify the Jakarta timezone
                        jakarta_timezone = pytz.timezone('Asia/Jakarta')

                        # Convert UTC time to Jakarta time
                        now_jakarta = datetime.now(jakarta_timezone)

                        # Format the date and time as desired
                        formatted_date_time = now_jakarta.strftime("%d/%m/%Y %H:%M:%S")

                        webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK"))
                        # you can set the color as a decimal (color=242424) or hex (color="03b2f8") number
                        embed = DiscordEmbed(title=f"Successfully Tapped!", description=f"**Balance:** {coins}\n **Taps:** +*{click}*\n\n **Total Taps:** {clicks}\n\n **DATE :** {formatted_date_time}", color="03b2f8")

                        # add embed object to webhook
                        webhook.add_embed(embed)

                        webhook.execute()
                    else:
                        self.log(f"Discord Webhook is not set!")

                if int(energy) < int(self.min_energy):
                    self.countdown(self.sleep)
                    continue

                print("~" * 50)
                self.countdown(self.interval)
                continue

            except (
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ConnectTimeout,
            ) as e:
                self.log(f"{merah} {e}")
                self.countdown(3)
                continue

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
            data = asyncio.run(self.login(phone))
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
