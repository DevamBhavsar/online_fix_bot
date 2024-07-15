import logging.config
import time
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from discord import Intents, Client, Message

# Discord bot token
DISCORD_TOKEN = "YOUR_TOKEN_HERE"


# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [PID %(process)d] [Thread %(thread)d] [%(levelname)s] [%(name)s] %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
})

LOGGER = logging.getLogger()
LOGIN_USERNAME = "YOUR_USERNAME"
LOGIN_PASSWORD = "YOUR_PASSWORD"
SITE_URL = "https://online-fix.me/games/"
options = Options()
options.add_argument("--headless")
driver_path = "/PATH/TO/chromedriver"
service = Service(executable_path=driver_path)

# Selenium function to search for a game
def search_game(game_name):
    driver = webdriver.Chrome(service=service, options=options)
    try:
        LOGGER.info("Requesting page " + SITE_URL)
        driver.get(SITE_URL)
    except TimeoutException:
        LOGGER.info("Page load timed out but continuing anyway")
    LOGGER.info("waiting for login fields")
    wait_until_visible(driver=driver, xpath="//input[@name = 'login_name']")
    LOGGER.info("Entering username and pwd")
    username_input = driver.find_element(by=By.XPATH, value="//input[@name = 'login_name']")
    username_input.send_keys(LOGIN_USERNAME)
    pwd_input = driver.find_element(by=By.XPATH, value="//input[@name='login_password']")
    pwd_input.send_keys(LOGIN_PASSWORD)
    LOGGER.info("Logging in ")
    driver.find_element(by=By.XPATH, value="//button[@onclick='dologin(); return false']").click()
    wait_until_visible(driver=driver, xpath="/html/body/header/div[2]/div/div[2]/div/a", duration=5)
    LOGGER.info("Successfully logged in")
    LOGGER.info(f"Searching for {game_name}")
    try:
        search_bar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "story"))
        )
        search_bar.send_keys(game_name + Keys.ENTER)
        LOGGER.info("Search performed successfully.")
    except TimeoutException:
        LOGGER.info("Timeout waiting for search bar to be clickable.")
    try:
        error_box = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "errors"))
        )
        error_description = error_box.find_element(By.CLASS_NAME, "description").text
        if "поиск по сайту не дал никаких результатов" in error_description:
            LOGGER.info("Game not found")
            return "Game not found"
    except TimeoutException:
        try:
            first_game_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.big-link"))
            )
            href_url = first_game_link.get_attribute('href')
            driver.get(href_url)
            LOGGER.info(f"Navigated to: {href_url}")
            LOGGER.info("Clicked on the first game link.")
            return f"Game found: {href_url}"
        except TimeoutException:
            LOGGER.info("Timeout waiting for first game link to be clickable.")
            return "Timeout waiting for first game link to be clickable."
        except ElementClickInterceptedException as e:
            LOGGER.info(f"Element click intercepted: {str(e)}")
            return f"Element click intercepted: {str(e)}"
        except Exception as e:
            LOGGER.info(f"Exception occurred: {str(e)}")
            return f"Exception occurred: {str(e)}"
    finally:
        driver.quit()

def wait_until_visible(driver, xpath=None, class_name=None, el_id=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
    elif el_id:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, el_id)))

# Discord bot setup
intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)

async def send_messages(message: Message, user_message: str) -> None:
    if not user_message:
        print("Message empty")
        return
    
    is_private = user_message[0] == "?"
    user_message = user_message[1:] if is_private else user_message

    try: 
        response = get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

def get_response(user_input: str) -> str:
    lowered = user_input.lower()

    if lowered == '':
        return "Say something"
    elif "hello" in lowered:
        return "Bing Chilling"
    elif lowered.startswith("!search_game "):
        game_name = user_input[len("!search_game "):].strip()
        return search_game(game_name)
    else:
        return "Command not recognized."

@client.event
async def on_ready() -> None:
    print(f"{client.user} is running")

@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    
    username = str(message.author)
    user_message = message.content
    channel = str(message.channel)

    print(f"[{channel}] {username} : '{user_message}'")
    await send_messages(message, user_message)

client.run(DISCORD_TOKEN)
