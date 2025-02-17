import time
import sys
import json
import os
import asyncio
from aiohttp import ClientSession, ClientTimeout
from datetime import datetime, timezone
from colorama import Fore, Style, init
from tabulate import tabulate

# Function to print banner with animations
def animated_banner():
    banner = """ 
    ██╗  ██╗ █████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗
    ██║ ██╔╝██╔══██╗╚══███╔╝██║   ██║██║  ██║██╔══██╗
    █████╔╝ ███████║  ███╔╝ ██║   ██║███████║███████║
    ██╔═██╗ ██╔══██║ ███╔╝  ██║   ██║██╔══██║██╔══██║
    ██║  ██╗██║  ██║███████╗╚██████╔╝██║  ██║██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
    """

    # Animation: Typing effect with delay for each line
    for line in banner.splitlines():
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.05)  # Small delay to create typing effect
        sys.stdout.write('\n')
        sys.stdout.flush()
        time.sleep(0.5)  # Delay between each line

    # Add a final effect after the banner
    sys.stdout.write(Fore.GREEN + "✨✨ Welcome to Kazuha's Teneo Bot ✨✨\n" + Style.RESET_ALL)
    sys.stdout.flush()

# Initialize Kazuha
init(autoreset=True)

class TeneoBot:
    def __init__(self):
        self.api_key = "OwAG3kib1ivOJG4Y0OCZ8lJETa6ypvsDtGmdhcjB"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }
        self.accounts = self.load_accounts()
        self.account_data = {}

    def load_accounts(self):
        """Membaca daftar akun dari account.txt"""
        accounts = []
        try:
            with open("accounts.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        email, password = line.split(":")
                        accounts.append((email, password))
        except FileNotFoundError:
            print(f"{Fore.RED}[ERROR] File account.txt tidak ditemukan!{Style.RESET_ALL}")
        return accounts

    async def user_login(self, email: str, password: str):
        """Melakukan login untuk mendapatkan token"""
        url = "https://auth.teneo.pro/api/login"
        data = json.dumps({"email": email, "password": password})
        headers = {**self.headers, "Content-Type": "application/json", "X-Api-Key": self.api_key}

        async with ClientSession(timeout=ClientTimeout(total=120)) as session:
            try:
                async with session.post(url, headers=headers, data=data) as response:
                    result = await response.json()
                    if response.status == 200 and "access_token" in result:
                        print(f"{Fore.GREEN}[ {email} ] ✅ GET Access Token Success{Style.RESET_ALL}")
                        return result["access_token"]
                    else:
                        print(f"{Fore.RED}[ {email} ] ❌ Login Failed: {result}{Style.RESET_ALL}")
                        return None
            except Exception as e:
                print(f"{Fore.RED}[ {email} ] ❌ Error Login: {e}{Style.RESET_ALL}")
                return None

    async def connect_websocket(self, email: str, token: str):
        """Menghubungkan WebSocket dengan token hasil login"""
        wss_url = f"wss://secure.ws.teneo.pro/websocket?accessToken={token}&version=v0.2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Upgrade": "websocket",
            "Connection": "Upgrade"
        }

        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=300)) as session:
                    async with session.ws_connect(wss_url, headers=headers) as wss:
                        print(f"{Fore.GREEN}[ {email} ] ✅ WebSocket Connected{Style.RESET_ALL}")

                        async def send_heartbeat():
                            while True:
                                await asyncio.sleep(10)
                                await wss.send_json({"type": "PING"})
                                self.print_ping_log(email)
                                await self.countdown_timer(email)  # Countdown per akun
                                self.display_status()  # Update tabel status akun

                        asyncio.create_task(send_heartbeat())

                        async for msg in wss:
                            response = json.loads(msg.data)

                            if response.get("message") in ["Connected successfully", "Pulse from server"]:
                                self.account_data[email] = {
                                    "Email": email,
                                    "Points Today": response.get("pointsToday", 0),
                                    "Total Points": response.get("pointsTotal", 0),
                                    "Last Update": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                }

            except Exception as e:
                print(f"{Fore.RED}[ {email} ] ❌ WebSocket Disconnected, Reconnecting in 5s...{Style.RESET_ALL}")
                await asyncio.sleep(5)

    def print_ping_log(self, email):
        """Menampilkan log PING secara rapi"""
        print(f"\n{Fore.CYAN}[ {email} ] 🔄 Sent PING to WebSocket{Style.RESET_ALL}")

    async def countdown_timer(self, email):
        """Menampilkan countdown sebelum update log terbaru"""
        for i in range(5, 0, -1):
            sys.stdout.write(f"\r{Fore.YELLOW}[ {email} ] 🔄 Refreshing in {i} sec...  ")
            sys.stdout.flush()
            await asyncio.sleep(1)
        sys.stdout.write("\r" + " " * 50 + "\r")  # Clear line setelah countdown selesai

    def display_status(self):
        """Membersihkan layar dan menampilkan status akun dalam tabel"""
        os.system("cls" if os.name == "nt" else "clear")  # Auto Clear Log

        if not self.account_data:
            return

        table_data = [
            [
                Fore.CYAN + v["Email"] + Style.RESET_ALL,
                Fore.YELLOW + str(v["Points Today"]) + Style.RESET_ALL,
                Fore.GREEN + str(v["Total Points"]) + Style.RESET_ALL,
                Fore.MAGENTA + v["Last Update"] + Style.RESET_ALL
            ]
            for v in self.account_data.values()
        ]

        print("\n" + Fore.YELLOW + "=" * 80)
        print(Fore.GREEN + "✨ TENEO BOT STATUS ✨".center(80))
        print(Fore.YELLOW + "=" * 80 + Style.RESET_ALL)
        print(tabulate(
            table_data,
            headers=[Fore.CYAN + "Email" + Style.RESET_ALL, Fore.YELLOW + "Points Today" + Style.RESET_ALL, Fore.GREEN + "Total Points" + Style.RESET_ALL, Fore.MAGENTA + "Last Update" + Style.RESET_ALL],
            tablefmt="double_outline"
        ))
        print("\n" + Fore.YELLOW + "=" * 80)

    async def process_accounts(self):
        """Proses login akun dan koneksi WebSocket"""
        tasks = []
        for email, password in self.accounts:
            token = await self.user_login(email, password)
            if token:
                tasks.append(self.connect_websocket(email, token))

        if tasks:
            await asyncio.gather(*tasks)

    async def main(self):
        print(f"{Fore.YELLOW}[ INFO ] 🔢 Total Akun: {len(self.accounts)}{Style.RESET_ALL}")
        await self.process_accounts()

if __name__ == "__main__":
    animated_banner()  # Display the animated banner
    bot = TeneoBot()
    asyncio.run(bot.main())
