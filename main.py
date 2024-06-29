
from urllib.parse import quote, unquote, urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import time
import random
from ChromeDriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tkinter import filedialog, messagebox, ttk, Tk, Label, Button, PhotoImage, simpledialog, font, Toplevel
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from PyQt5.QtWidgets import QFileDialog, QApplication
from PIL import Image, ImageTk
from twocaptcha import TwoCaptcha
from tqdm import tqdm
import pandas as pd
import xlsxwriter
import logging
import string
import urllib3
import chardet
import datetime
import psutil
import urllib
import base64
import glob
import sys
import os
import io


class SearchAboutNews(Tk):

    def start_driver(self):
        self.driver = WebDriver.start_driver(self)
        return self.driver

    def get_search_links(self, words_file_path):
        encodings = ['utf-8', 'latin-1', 'utf-16', 'utf-32', 'iso-8859-1',
                     'windows-1252']
        for encoding in encodings:
            try:
                with open(words_file_path, 'r', encoding=encoding) as file:
                    words = file.readlines()
                return list(words)
            except UnicodeDecodeError:
                continue

    def get_words_from_file(self, words_file_path):
        encodings = ['utf-8', 'latin-1', 'utf-16', 'utf-32', 'iso-8859-1', 'windows-1252']
        for encoding in encodings:
            try:
                with open(words_file_path, 'r', encoding=encoding) as file:
                    words = file.readlines()
                return [line.strip() for line in words]
            except UnicodeDecodeError:
                continue

    def select_file(self):
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select Search Engine Links File",
                                               filetypes=[("Text files", "*.txt")])
        return file_path

    def select_time_option(self):
        time_option = simpledialog.askstring("Time Option",
                                             "Enter the time option ('An', 'd', 'w', 'm', '6m', 'y'):")
        return time_option

    def select_max_results(self):
        max_results = simpledialog.askinteger("Max Results",
                                              "Enter the maximum number of results to fetch:")
        return max_results

    def search_google(self, word, search_link, time_option='anytime', max_results='5'):
        found_links = []
        processed_urls = set()
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        start = 0

        while len(found_links) < max_results:
            encoded_word = quote(word)
            search_url = f"{search_link}{encoded_word}"
            if time_option != 'anytime':
                search_url += f"&tbs=qdr:{time_option}"

            try:
                response = requests.get(search_url, headers=headers)
                response.raise_for_status()

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    search_results = soup.find_all("a")
                    for result in search_results:
                        href = result.get("href")
                        if href and href.startswith("/url?q="):
                            url = href.split("/url?q=")[1].split("&sa=")[0]
                            url = unquote(url)
                            if url not in processed_urls and not url.startswith(
                                    ('data:image', 'javascript', '#', 'https://maps.google.com/',
                                     'https://accounts.google.com/', 'https://www.google.com/preferences',
                                     'https://policies.google.com/', 'https://support.google.com/')):
                                found_links.append({'link': url})
                                processed_urls.add(url)
                                if len(found_links) >= max_results:
                                    break

                start += 1
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error occurred: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        return found_links

    def search_yahoo(self, word, search_link, time_option='anytime', max_results='5'):
        found_links = []
        processed_urls = set()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        start = 0

        while len(found_links) < max_results:
            encoded_word = quote(word)
            search_url = f"{search_link}{encoded_word}"
            if time_option != 'anytime':
                search_url += f"&btf={time_option}"

            try:
                response = requests.get(search_url, headers=headers)
                response.raise_for_status()

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    search_results = soup.find_all("div", class_="algo-sr")
                    for result in search_results:
                        link_tag = result.find("a")
                        if link_tag:
                            href = link_tag.get("href")
                            if href and href not in processed_urls:
                                found_links.append({'link': href})
                                processed_urls.add(href)
                                if len(found_links) >= max_results:
                                    break

                start += 10
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error occurred: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        return found_links

    def search_duckduckgo(self, word, search_link, time_option, max_results='5'):
        found_links = []
        processed_urls = set()

        encoded_word = quote(word)
        search_url = f"{search_link}{encoded_word}"
        driver = self.start_driver()
        driver.get(search_url)
        page_count = 0

        while len(found_links) < max_results:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.result__a"))
                )

                links_found = 0
                search_results = driver.find_elements(By.CSS_SELECTOR, "a.result__a")
                for result in search_results:
                    href = result.get_attribute("href")
                    if href and href not in processed_urls:
                        found_links.append({'link': href})
                        processed_urls.add(href)
                        links_found += 1
                        if len(found_links) >= max_results:
                            break

                next_button = driver.find_element(By.CSS_SELECTOR, "input.btn.btn--alt[value='Next']")
                if next_button:
                    next_button.click()
                    time.sleep(random.uniform(1.0, 3.0))
                else:
                    break

                if links_found == 0:
                    break

                page_count += 1

            except Exception as e:
                print(f"An error occurred: {e}")
                break

        driver.quit()
        return found_links


    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'\W+', ' ', text)
        return text

    def compute_similarity(self, text1, text2):
        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        return cosine_similarity(vectors)[0, 1]

    def check_word_in_link(self, link, word, threshold=0.001):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(link, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                page_content = self.preprocess_text(response.text)
                word = self.preprocess_text(word)
                similarity = self.compute_similarity(page_content, word)
                return similarity
        except Exception as e:
            print(f"An error occurred while checking the link {link}: {e}")
            return 0.0

    def check_word_in_link_with_selenium(self, link, word, threshold=0.0001):
        try:
            driver = self.start_driver()
            driver.get(link)
            time.sleep(2)
            page_content = driver.page_source

            page_content = self.preprocess_text(page_content)
            word = self.preprocess_text(word)
            similarity = self.compute_similarity(page_content, word)

            driver.quit()

            return similarity

        except Exception as e:
            print(f"An error occurred while checking the link {link}: {e}")
            return 0.0





if __name__ == "__main__":
    app = SearchAboutNews()
    app.execute_task()