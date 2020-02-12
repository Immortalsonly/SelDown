import os
import time
import logging
import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class SelDown:
    def __init__(self, driverpath):
        """Simple wrapper for selenium to make downloading automation easier."""
        logging.info('Starting Session')
        self.driverpath = driverpath
        self.chrome_options = Options()
        # add the options to the driver that allow downloading/uploading
        experimental_options = ("prefs", {"download.prompt_for_download": False, "download.directory_upgrade": True,
                                          "safebrowsing_for_trusted_sources_enabled": False, "safebrowsing.enabled": False, 'select_file_dialogs.allowed': False})
        arguments = ["--headless", "--window-size=3840x2160",
                     "--disable-notifications", "--silent"]
        for argument in arguments:
            self.chrome_options.add_argument(argument)
        for value in experimental_options:
            self.chrome_options.add_experimental_option("prefs", value)
        self.driver = webdriver.Chrome(chrome_options=self.chrome_options, executable_path=self.driverpath, service_args=[
                                       "--log-path=logs/chromium.log"])

    def login(self, login_page, email_element_name, useremail, password_element_name, userpassword):
        """Allows login in to a given page by interacting with form elements by name

        login_page -- url.
        email_element_name -- css name attribute of the email form.
        password_element name -- css name attribute of the password form.
        """
        try:
            self.driver.get(login_page)
            logging.info('Attempting login to: {}'.format(
                self.driver.current_url))
        except WebDriverException:
            logging.error(
                'Webdriver unable to initialize (webdriver not found)')
        try:
            email = self.driver.find_element_by_name(email_element_name)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.NAME, email_element_name)))
            email.send_keys(useremail)
            try:
                pw = self.driver.find_element_by_name(password_element_name)
                pw.send_keys(userpassword)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, password_element_name)))
            except NoSuchElementException:
                logging.error('Element not found')
        except NoSuchElementException:
            logging.error('Element not found')
        except TimeoutException:
            logging.warning('Loading took too long. trying again.')
        finally:
            email.submit()
            logging.info('Login succes. Current page: {}'.format(
                self.driver.current_url))

    def navigate(self, *args):
        """Navigate to any number of urls."""
        for page in args:
            self.driver.get(page)
            logging.info('Navigating to: {}'.format(self.driver.current_url))

    def interact(self, *args):
        """interact with a clickable element. 
        args: xpath of the element(s)"""
        try:
            for element in args:
                self.driver.find_element_by_xpath(element).click()
        except NoSuchElementException:
            logging.warning('Element not found.')
        
    def fill(self, element, text, use_name=True):
        """Fill a form"""
        try:
            if use_name == True:
                fillable_form = self.driver.find_element_by_name(element)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, element)))
            else:
                fillable_form = self.driver.find_element_by_xpath(element)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, element)))
        except NoSuchElementException:
            logging.error('Element not found.')
        finally:
            fillable_form.send_keys(text)

    def download(self, download_directory, *args, use_url=True):
        """Download files based on a given url or xpath.

        download_directory: directory of where the file will be saved. 
        use_url = use urls or xpath. (Default is url)
        args: urls of files to download.
        """
        self.driver.command_executor._commands["send_command"] = (
            "POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {
            'behavior': 'allow', 'downloadPath': download_directory}}
        self.driver.execute("send_command", params)

        for file in tqdm.tqdm(args, desc="Downloading"):
            try:
                if use_url == True:
                    getfile = self.driver.get(file)
                else:
                    getfile = self.driver.find_element_by_xpath(file)
                getfile.click()
                time.sleep(2)
            except AttributeError:
                # This usually doesn't stop the download, so it can be ignored.
                time.sleep(2)
            finally:
                logging.info('file downloaded to {}'.format(
                    download_directory))

    def unstable(self):
        """Untested things.""" 
        def upload(self, filepath, element):
            """Upload files by bypassing the fileselector menu

            filepath: relative path to the file.
            element: classname of the element 
            """
            try:
                absolute_filepath = os.path.abspath(filepath)
            except IOError:
                logging.error(
                    'sytem was not able to find the file specified. did you use an absolute path and double slash? (//)')
            #uploadfields are usually hidden, they need to be 'visible' for selenium to interact with.
            make_visible = [
                'document.getElementsByClassName("{}").style.display="visible";'.format(element),
                'document.getElementsByClassName("{}").style.display="block";'.format(element),
                'document.getElementsByClassName("{}").style.position="absolute";'.format(element),
                'document.getElementsByClassName("{}").style.top="10px";'.format(element),
                'document.getElementsByClassName("{}").style.height="20px";'.format(element),
                'document.getElementsByClassName("{}").style.width="20px";'.format(element),
            ]
            try:
                for line in make_visible:
                    self.driver.execute_script(line)
            except NoSuchElementException:
                for line in next(make_visible):
                    self.driver.execute_script(line)
            finally:
                uploadfile = self.driver.find_element_by_class_name(element)
                uploadfile.send_keys(absolute_filepath)

    def expose_driver(self):
        """Expose the webdriver used by selenium.

        this simply returns the driver. useful if you want to use selenium directly.
        """
        return self.driver

    def end(self):
        """Ends the driver session."""
        try:
            self.driver.quit()
            logging.info('session ended')
        except WebDriverException:
            logging.error('Webdriver already quit or never started.')

