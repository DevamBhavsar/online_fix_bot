"""
Searches for a game on the specified website, logs in, performs the search, and retrieves the game's download link and store name.

Args:
    game_name (str): The name of the game to search for.

Returns:
    tuple: A tuple containing the store name, game link, and the path to the downloaded .torrent file, or `(None, None, None)` if the game is not found or an error occurs.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import logging.config
import time
from lxml import html
from discord import Intents, File
from discord.ext import commands
import os
from dotenv import load_dotenv


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
        "handlers": [
            "console"
        ]
    }
})

def wait_until_visible(driver, xpath=None, class_name=None, el_id=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
    elif el_id:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, el_id)))

load_dotenv()
LOGGER = logging.getLogger()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
LOGIN_USERNAME = os.getenv('LOGIN_USERNAME')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')
SITE_URL = os.getenv('SITE_URL')
DRIVER_PATH = os.getenv('DRIVER_PATH')
DOWNLOADS_DIR = os.getenv('DOWNLOADS_DIR')

options = Options()
options.add_argument("--headless=new")
service = Service(executable_path=DRIVER_PATH)


async def search_game(game_name: str) -> tuple:
    driver = webdriver.Chrome(service=service, options=options)
    store_name = None
    game_link = None  # Initialize for storing the game link

    try:
        LOGGER.info("Requesting page " + SITE_URL)
        driver.get(SITE_URL)
    except TimeoutException:
        LOGGER.info("Page load timed out but continuing anyway")
        
    LOGGER.info("Waiting for login fields")
    wait_until_visible(driver=driver, xpath="//input[@name='login_name']")
    
    LOGGER.info("Entering username and pwd")
    username_input = driver.find_element(by=By.XPATH, value="//input[@name='login_name']")
    username_input.send_keys(LOGIN_USERNAME)
    
    pwd_input = driver.find_element(by=By.XPATH, value="//input[@name='login_password']")
    pwd_input.send_keys(LOGIN_PASSWORD)
    
    LOGGER.info("Logging in")
    driver.find_element(by=By.XPATH, value="//button[@onclick='dologin(); return false']").click()
    
    wait_until_visible(driver=driver, xpath="/html/body/header/div[2]/div/div[2]/div/a", duration=5)
    LOGGER.info("Successfully logged in")
    
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
            return None, None, None
    except TimeoutException:
        try:
            first_game_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.big-link"))
            )
            game_link = first_game_link.get_attribute('href')  # Get the game link
            href_url = first_game_link.get_attribute('href')
            driver.get(href_url)
            LOGGER.info(f"Navigated to: {href_url}")
            LOGGER.info("Clicked on the first game link.")
        except TimeoutException:
            LOGGER.info("Timeout waiting for first game link to be clickable.")
            return None, None, None
        except ElementClickInterceptedException as e:
            LOGGER.info(f"Element click intercepted: {str(e)}")
            return None, None, None
        except Exception as e:
            LOGGER.info(f"Exception occurred: {str(e)}")
            return None, None, None

    try:
        store_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="dle-content"]/div/article/div[2]/div[3]/a[1]'))
        )
        store_name = store_element.text
        LOGGER.info(f"Store: {store_name}")
    except TimeoutException:
        LOGGER.info("Timeout waiting for the store element to be visible.")
    except NoSuchElementException:
        LOGGER.info("Store element not found.")
    except Exception as e:
        LOGGER.info(f"Exception occurred: {str(e)}")

    try:
        button_link = driver.find_element(by=By.XPATH, value="//a[@class='btn btn-success btn-small' and text()='Скачать Torrent']")
        button_link.click()
        windows = driver.window_handles
        LOGGER.info(f"List of windows = {windows}")
        driver.switch_to.window(windows[1])
        LOGGER.info(f"Current tab = {driver.current_url}")
        link = driver.find_element(By.XPATH, "//a[contains(@href, 'OFME')]")
        link.click()   
        torrent_page = driver.page_source
        html_page = html.fromstring(torrent_page)
        link = html_page.xpath("//a[contains(@href, 'OFME')]")
        ofme_link = link[0].get('href') if link else None
        LOGGER.info(ofme_link) 
        file_name = ofme_link[:-len(".torrent")]
        LOGGER.info(f"File name to search: {file_name}")    
        time.sleep(5)
        
        for root, dirs, files in os.walk(DOWNLOADS_DIR):
            for file in files:
                if file_name in file:
                    return store_name, game_link, os.path.join(root, file)
        return store_name, game_link, None
    except TimeoutException:
        LOGGER.info("Timeout waiting for the Download Torrent button to be clickable.")
    finally:
        driver.quit()

    return store_name, game_link, None

# Discord bot setup
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=["!", "?"], intents=intents, help_command=None)

@bot.event
async def on_ready():
    LOGGER.info(f"{bot.user} is running")

@bot.command(name="search_game")
async def search_game_command(ctx, *, game_name: str):
    is_private = ctx.message.content.startswith("?")
    await ctx.author.send("Searching for the game. I'll let you know when it's ready.") if is_private else await ctx.send("Searching for the game. I'll let you know when it's ready.")    
    store_name, game_link, torrent_file_path = await search_game(game_name)
    if torrent_file_path:
        if is_private:
            await ctx.author.send(f"The game is for {store_name}.", file=File(torrent_file_path))
            await ctx.author.send(f"Game Link: {game_link}")
        else:
            await ctx.send(f"The game is for {store_name}.", file=File(torrent_file_path))
            await ctx.send(f"Game Link: {game_link}")
    else:
        await ctx.send("Couldn't find the game or failed to download the .torrent file.")
@bot.command(name="help")
async def help_command(ctx):
    help_message = """
    **Online Fix Bot Commands**
    
    !search_game <game name> - Search for a game and download its torrent file
    !help - Display this help message
    
    Use ? instead of ! for private responses.
    """
    await ctx.send(help_message)

bot.run(DISCORD_TOKEN)


