from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

site_login_username = "YOUR_USERNAME"
site_login_pwd = "YOUR_PASSWORD"

options = Options()
driver_path = 'YOUR_PATH_TO_CHROME_DRIVER'
service = Service(executable_path=driver_path)

driver = webdriver.Chrome(service=service, options=options)

# Open the website
driver.get("https://online-fix.me/games/")

try:
    login_form = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "/html/body/header/div[2]/div/div[2]"))
    )
    login_username = driver.find_element(By.NAME, "login_name")
    login_username.send_keys(site_login_username)
    login_pwd = driver.find_element(By.NAME, "login_password")
    login_pwd.send_keys(site_login_pwd)
    login_button = driver.find_element(By.XPATH, "/html/body/header/div[2]/div/div[2]/form/div[1]/button[1]")
    login_button.click()
    print("Successfully logged in.")
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element(login_button)
    )
    driver.refresh()
except TimeoutException:
    print("Already logged in or login not required.")

# Wait for the search bar to be clickable
game_name = input("Enter Game name: ")
try:
    search_bar = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "story"))
    )
    search_bar.send_keys(game_name + Keys.ENTER)
    print("Search performed successfully.")
except TimeoutException:
    print("Timeout waiting for search bar to be clickable.")

# Check if the error box is displayed
try:
    error_box = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "errors"))
    )
    error_description = error_box.find_element(By.CLASS_NAME, "description").text
    if "поиск по сайту не дал никаких результатов" in error_description:
        print("Game not found")
except TimeoutException:
    # No error box found, proceed to click on the first game link
    try:
        first_game_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[1]/div/div[2]/div[3]/div/a"))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'});", first_game_link)
        first_game_link.click()
        print("Clicked on the first game link.")
    except TimeoutException:
        print("Timeout waiting for first game link to be clickable.")
    except ElementClickInterceptedException as e:
        print(f"Element click intercepted: {str(e)}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

# Extract and print the store information
try:
    store_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="dle-content"]/div/article/div[2]/div[3]/a[1]'))
    )
    store_name = store_element.text
    print(f"Store: {store_name}")
except TimeoutException:
    print("Timeout waiting for the store element to be visible.")
except NoSuchElementException:
    print("Store element not found.")
except Exception as e:
    print(f"Exception occurred: {str(e)}")

# Click on the button
try:
    button_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[1]/div/div[2]/div/article/div[2]/div[3]/div[2]/div/a[4]'))
    )
    button_element.click()
    print("Button clicked successfully.")
except TimeoutException:
    print("Timeout waiting for the button to be clickable.")
except ElementClickInterceptedException as e:
    print(f"Element click intercepted: {str(e)}")
except Exception as e:
    print(f"Exception occurred: {str(e)}")

# Now find and print the torrent link
try:
    link_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/pre/a[2]'))
    )
    link = link_element.get_attribute('href')
    print(f"Torrent link: {link}")
except TimeoutException:
    print("Timeout waiting for the link to be clickable.")
except ElementClickInterceptedException as e:
    print(f"Element click intercepted: {str(e)}")
except Exception as e:
    print(f"Exception occurred: {str(e)}")

# Close the browser session
driver.quit()

