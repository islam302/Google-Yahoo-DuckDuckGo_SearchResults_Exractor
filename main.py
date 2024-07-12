from tkinter import filedialog, Button, Label, PhotoImage, font, simpledialog, messagebox, Tk
from bs4 import BeautifulSoup
import time
import random
import ttkbootstrap as TTK
from ChromeDriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import tkinter as tk
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from PIL import Image, ImageTk
import pandas as pd
import xlsxwriter
import logging
import chardet
import datetime
import psutil
import urllib
import requests
import base64
import glob
import sys
import os
from urllib.parse import quote, unquote


class SearchAboutNews(Tk):

    def __init__(self):
        super().__init__()

        self.title("Searching Links Maker")
        self.geometry("550x600")
        self.configure(bg="#282828")
        self.style = TTK.Style()
        self.style.theme_use("darkly")
        self.style.configure('TButton', background='blue', foreground='white')

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15',
        ]

        self.driver = None
        self.current_dir = os.path.dirname(sys.argv[0])
        self.results_folder = os.path.join(self.current_dir, 'RESULTS')
        os.makedirs(self.results_folder, exist_ok=True)

        self.create_widgets()

    def encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

    def execute_task(self):
        try:
            news_articles = self.get_words_from_file('words.txt')
            if not news_articles:
                messagebox.showinfo("Error", "No words in this file")
                return

            messagebox.showinfo("Select file", "Select Search links file")
            file = self.select_file()
            search_links = self.get_search_links(file)

            if not search_links:
                print("No search links found.")
                return

            time_option = self.select_time_option()

            if not time_option:
                return

            max_results = self.select_max_results()

            messagebox.showinfo("Select file", "Select Excluded links file")

            domains_file = self.select_file()
            excluded_domains = self.get_excluded_domains(domains_file)

            for i, (news_title, news_article) in enumerate(news_articles, start=1):
                if not news_title:
                    print(f"Skipping article {i} due to missing title")
                    continue

                folder_name_input = news_title.strip('##')
                now = datetime.datetime.now()
                formatted_now = now.strftime("%Y-%m-%d & %H-%M")
                folder_name = f'{folder_name_input}-{formatted_now}-Search'.replace(':', '-').replace('"', '').encode(
                    'utf-8').decode('utf-8')
                folder_path = os.path.join(self.results_folder, folder_name)
                os.makedirs(folder_path, exist_ok=True)

                self.main(folder_name_input, folder_path, news_article, search_links, time_option, max_results, excluded_domains)

            messagebox.showinfo("Task Completed", "Task completed successfully!")
        except Exception as e:
            messagebox.showinfo("Error", f"{e}")

    def create_widgets(self):
        label = tk.Label(self, text="Welcome to Boot Get Searching Links", font=("Arial", 16), bg="#282828", fg="white")
        label.pack(pady=15)

        current_dir = os.path.dirname(sys.argv[0])
        logo_files = glob.glob(os.path.join(current_dir, "logo.*"))
        if logo_files:
            logo_path = logo_files[0]
            try:
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((260, 260), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                logo_label = tk.Label(self, image=logo_photo, bg="#282828")
                logo_label.image = logo_photo
                logo_label.pack()
            except Exception as e:
                print(f"Error loading image: {e}")
                messagebox.showerror("Error", "Failed to load logo image")

        label_tasks = Label(self, text='Select a task to execute:', font=('Arial', 16), bg='#282828', fg='white')
        label_tasks.pack(pady=10)

        custom_font = font.Font(family="Helvetica", size=12, weight="bold")

        btn_style = {
            'bg': '#006400',
            'fg': 'white',
            'padx': 10,
            'pady': 5,
            'bd': 0,
            'borderwidth': 0,
            'highlightthickness': 0,
            'font': custom_font
        }

        def on_enter_task2(e):
            self.task2_button.config(bg="#004d00")

        def on_leave_task2(e):
            self.task2_button.config(bg="#006400")

        self.task2_button = Button(self, text='Run Searching TASK', command=self.execute_task, **btn_style)
        self.task2_button.pack(pady=10)
        self.task2_button.bind("<Enter>", on_enter_task2)
        self.task2_button.bind("<Leave>", on_leave_task2)

        exit_button = tk.Button(self, text="Exit", command=self.destroy, bg="red", fg="white", font=("Arial", 17))  # Medium font size
        exit_button.pack(pady=15)

    def get_words_from_file(self, words_file_path):
        encodings = ['utf-8', 'latin-1', 'utf-16', 'utf-32', 'iso-8859-1', 'windows-1252']
        for encoding in encodings:
            try:
                with open(words_file_path, 'r', encoding=encoding) as file:
                    lines = file.read().splitlines()
                news_articles = []
                current_article = []
                current_title = None
                for line in lines:
                    if line.startswith('##') and line.endswith('##'):
                        if current_article:
                            news_articles.append((current_title, current_article))
                        current_article = []
                        current_title = line.strip()
                    else:
                        current_article.append(line)
                if current_article:
                    news_articles.append((current_title, current_article))
                return news_articles
            except Exception as e:
                print(f"Error reading file with encoding {encoding}: {e}")
        return []

    def start_driver(self):
        self.driver = WebDriver.start_driver(self)
        return self.driver

    def get_publish_date(self, link):
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        try:
            response = requests.get(link)
            if response.status_code == 200:
                encoding = chardet.detect(response.content)['encoding']
                response.encoding = encoding
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')

                link_text = soup.get_text()
                date_match = re.search(r'\b\d{1,2}\s+\w+\s+\d{4}\b', link_text, re.IGNORECASE | re.UNICODE)
                if date_match:
                    link_date = date_match.group()
                    return link_date.strip()

                date_patterns = [
                    r'\b(\d{4}/\d{2}/\d{2})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{2,4})\b',
                    r'\b(\d{4}-\d{2}-\d{2})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{4})\b',
                    r'\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{2,4})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2})\b',
                    r'\b(\d{1,2}\s+\w+\s+/\s+\w+\s+\d{2,4})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}\s+[?-?]+\s+\d{4})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\s+[?-?]+\s+\d{1,2}:\d{2}\b',
                    r'\b(\d{1,2}\s+[\u0623-\u064a]+\s+\d{4})\b',
                    r'\b(\d{1,2}\s+[\u0623-\u064a]+\s+/\s+[\u0623-\u064a]+\s+\d{2,4})\b',
                    r'(\d{4}/\d{2}/\d{2}/)'
                ]

                for pattern in date_patterns:
                    date_match = re.search(pattern, html_content, re.IGNORECASE | re.UNICODE)
                    if date_match:
                        link_date = date_match.group()
                        return link_date.strip()

                time_tags = soup.find_all('time', class_=re.compile(r'.*'))
                for time_tag in time_tags:
                    datetime_attr = time_tag.get('datetime')
                    if datetime_attr:
                        arabic_date = time_tag.text.strip()
                        return arabic_date

                link_date_match = re.search(r'(\d{4}-\d{2}-\d{2})', link)
                if link_date_match:
                    return link_date_match.group()

            return None
        except:
            return None

    def get_title(self, link):
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            response = requests.get(link)
            if response.status_code == 200:
                encoding = chardet.detect(response.content)['encoding']
                response.encoding = encoding
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                title = soup.title.string.strip()
                return title
        except:
            return None

    def killDriverZombies(self, driver_pid):
        try:
            parent_process = psutil.Process(driver_pid)
            children = parent_process.children(recursive=True)
            for process in [parent_process] + children:
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

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

    def get_excluded_domains(self, domains_file):
        try:
            with open(domains_file, 'r') as file:
                excluded_domains = [line.strip() for line in file.readlines()]
            return excluded_domains
        except FileNotFoundError:
            print(f"Domains file '{domains_file}' not found.")
            return []

    def search_google(self, word, search_link, time_option='anytime', max_results='10'):
        found_links = []
        processed_urls = set()
        start = 0

        while len(found_links) < max_results:
            encoded_word = quote(word)
            search_url = f"{search_link}{encoded_word}&start={start}"
            if time_option != 'anytime':
                search_url += f"&tbs=qdr:{time_option}"

            try:
                response = requests.get(search_url)
                response.raise_for_status()

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    search_results = soup.find_all("a")
                    links_found = 0

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
                                links_found += 1
                                if len(found_links) >= max_results:
                                    break

                    if links_found == 0:
                        break  # No new links found, exit the loop

                start += 10
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error occurred: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        return found_links

    def search_yahoo(self, word, search_link, time_option='anytime', max_results='10'):
        found_links = []
        processed_urls = set()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        start = 0

        while len(found_links) < max_results:
            encoded_word = quote(word)
            search_url = f"{search_link}{encoded_word}&b={start}"
            if time_option != 'anytime':
                search_url += f"&btf={time_option}"

            try:
                response = requests.get(search_url, headers=headers)
                response.raise_for_status()

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    search_results = soup.find_all("div", class_="algo-sr")
                    links_found = 0

                    for result in search_results:
                        link_tag = result.find("a")
                        if link_tag:
                            href = link_tag.get("href")
                            if href and href not in processed_urls:
                                found_links.append({'link': href})
                                processed_urls.add(href)
                                links_found += 1
                                if len(found_links) >= max_results:
                                    break

                    if links_found == 0:
                        break  # No new links found, exit the loop

                start += 10
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error occurred: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        return found_links

    def search_duckduckgo(self, word, search_link, time_option='anytime', max_results='10'):
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

                next_button = driver.find_element(By.CSS_SELECTOR, "input.btn.btn--alt")
                if not next_button:
                    break  # No more pages, exit the loop

                next_button.click()
                time.sleep(random.uniform(1.0, 3.0))  # Introduce random delay between 1 to 3 seconds

                if links_found == 0:
                    break

                page_count += 1

            except Exception as e:
                print(f"An error occurred: {e}")
                break

        driver.quit()
        return found_links

    def main(self, file_name_input, folder_path, search_words, search_links, time_option, max_results, excluded_domains):
        self.start_driver()
        for search_word in search_words:
            found_links_all = []

            for search_link in search_links:
                if 'google' in search_link:
                    found_links_all.extend(self.search_google(search_word, search_link, time_option, max_results))
                elif 'yahoo' in search_link:
                    found_links_all.extend(self.search_yahoo(search_word, search_link, time_option, max_results))
                elif 'duckduckgo' in search_link:
                    found_links_all.extend(self.search_duckduckgo(search_word, search_link, time_option, max_results))

            filtered_links = [link for link in found_links_all if not any(domain in link['link'] for domain in excluded_domains)]

            now = datetime.datetime.now()
            formatted_now = now.strftime("%Y-%m-%d & %H-%M")

            # Generate a safe file name without problematic characters
            search_word_safe = search_word.replace(':', '-').replace('"', '')
            # Limit the length of the search word part to ensure overall length limit
            max_search_word_length = 30  # Example: Limit search word length to 30 characters
            truncated_search_word = search_word_safe[:max_search_word_length]

            # Construct file name with a truncated search word
            file_name = f'{truncated_search_word}-{formatted_now}-Search-Data.xlsx'
            excel_path = os.path.join(folder_path, file_name)

            # Create Excel file and save data
            df_all_data = pd.DataFrame(filtered_links)
            writer_all = pd.ExcelWriter(excel_path, engine='xlsxwriter')
            df_all_data.to_excel(writer_all, index=False)
            worksheet_all = writer_all.sheets['Sheet1']
            worksheet_all.set_column('A:Z', 50)
            writer_all._save()

        if self.driver:
            driver_pid = self.driver.service.process.pid
            self.killDriverZombies(driver_pid)


if __name__ == "__main__":
    app = SearchAboutNews()
    app.mainloop()



