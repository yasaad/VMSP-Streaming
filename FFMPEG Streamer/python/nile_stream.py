from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
def startNileStream():
    PATH= r"C:\\Program Files (x86)\\chromedriver.exe"
    op = Options()
    op.add_argument("--headless")
    op.add_argument("--disable-gpu")
    driver = webdriver.Chrome(PATH, options=op)
    print("Setup Nile Stream")
    try:
        driver.get("https://control.smc-host.com/accounts.aspx")

        email = driver.find_element_by_id("content_txtLoginEmail")
        password = driver.find_element_by_id("content_txtLoginPassword")

        email.send_keys("streaming@vmspchurch.org")
        password.send_keys("password1")
        password.send_keys(Keys.RETURN)
        # Wait for page to load
        facebook_live = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "content_btnFBSave")))
        facebook_live.click()
        # Wait for page to load
        select_elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "content_ddSourceTV")))
        channel_selector = Select(select_elem)
        print(f"Channel: {channel_selector.first_selected_option.text}")
        stream_key = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "content_txtYTstream")))
        print(f"Stream Key: {stream_key.get_attribute('value')}")

        start_yt_stream = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "content_btnYTStart")))
        start_yt_stream.click()
    finally:
        print("Done")
        driver.quit()
