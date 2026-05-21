from playwright.sync_api import sync_playwright
import os
import time

SESSION_FILE = "whatsapp_session.json"


class WhatsAppBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):

        self.playwright = sync_playwright().start()

        if os.path.exists(SESSION_FILE):

            self.browser = self.playwright.chromium.launch(
                headless=False
            )

            self.context = self.browser.new_context(
                storage_state=SESSION_FILE
            )

        else:

            self.browser = self.playwright.chromium.launch(
                headless=False
            )

            self.context = self.browser.new_context()

        self.page = self.context.new_page()

        self.page.goto("https://web.whatsapp.com")

    def login(self):

        if not os.path.exists(SESSION_FILE):

            print("Escanea el QR...")

            self.page.wait_for_selector(
                '[data-testid="chat-list"]',
                timeout=120000
            )

            self.context.storage_state(
                path=SESSION_FILE
            )

            print("Sesion guardada")

        else:

            self.page.wait_for_selector(
                '[data-testid="chat-list"]'
            )

            print("Sesion reutilizada")

    def send_message(
        self,
        phone,
        message
    ):

        url = (
            f"https://web.whatsapp.com/send?"
            f"phone={phone}"
        )

        self.page.goto(url)

        self.page.wait_for_selector(
            '[contenteditable="true"]'
        )

        time.sleep(2)

        box = self.page.locator(
            '[contenteditable="true"]'
        ).last

        box.fill(message)

        box.press("Enter")

        print("Mensaje enviado")

    def close(self):

        self.browser.close()
        self.playwright.stop()


if __name__ == "__main__":

    bot = WhatsAppBot()

    bot.start()

    bot.login()

    bot.send_message(
        "569XXXXXXXX",
        "⚠️ Stock bajo: Coca Cola 350ml"
    )

    input("ENTER para cerrar...")

    bot.close()
