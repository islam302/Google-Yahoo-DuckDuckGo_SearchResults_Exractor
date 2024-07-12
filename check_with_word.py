import os
import sys
import tkinter as tk
from tkinter import Tk, Label, Button, BooleanVar, filedialog, font, messagebox
import glob
import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image, ImageTk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ttkbootstrap as TTK
from ChromeDriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import base64
import psutil


class SearchAboutNews(Tk):

    def __init__(self):
        super().__init__()

        self.title("Searching Links Maker")
        self.geometry("550x700")
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
                print("No search words")
                return
            file = self.select_file()
            links = self.get_links_from_excel(file)

            similarity_threshold = 0.01
            for i, (news_title, news_article) in enumerate(news_articles, start=1):
                if not news_title:
                    print(f"Skipping article {i} due to missing title")
                    continue

                folder_name_input = news_title.strip('##')
                now = datetime.datetime.now()
                formatted_now = now.strftime("%Y-%m-%d & %H-%M")
                folder_name = f'{folder_name_input}-{formatted_now}-Check-word'.replace(':', '-').replace('"', '').encode(
                    'utf-8').decode('utf-8')
                folder_path = os.path.join(self.results_folder, folder_name)
                os.makedirs(folder_path, exist_ok=True)

                self.main(folder_name_input, folder_path, news_article, links, similarity_threshold)

            messagebox.showinfo("Task Completed", "Task completed successfully!")
        except Exception as e:
            print(f"Error occurred: {e}")
            messagebox.showinfo("Error", f"An error occurred: {e}")

    def create_widgets(self):
        label = tk.Label(self, text="Welcome to Checker BOT", font=("Arial", 16), bg="#282828", fg="white")
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

        self.include_iframe_var = BooleanVar()
        self.include_iframe_checkbutton = tk.Checkbutton(self, text="With Frames", variable=self.include_iframe_var,
                                                         bg="#282828", fg="white", selectcolor="#282828",
                                                         font=("Arial", 15))  # Medium font size
        self.include_iframe_checkbutton.pack(pady=10)

        label_tasks = Label(self, text='Start The Task:', font=('Arial', 16), bg='#282828', fg='white')
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

    def start_driver(self):
        self.driver = WebDriver.start_driver(self)
        return self.driver

    def killDriverZombies(self, driver_pid):
        try:
            parent_process = psutil.Process(driver_pid)
            children = parent_process.children(recursive=True)
            for process in [parent_process] + children:
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    def select_file(self):
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select Search Engine Links File",
                                               filetypes=[("Text files", "*.xlsx")])
        return file_path

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

    def get_links_from_excel(self, file_path, column_name='link'):
        try:
            df = pd.read_excel(file_path)
            if column_name not in df.columns:
                raise ValueError(f"Column '{column_name}' not found in the Excel file.")

            links = df[column_name].tolist()
            return links
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return []

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
                if similarity >= threshold:
                    return True
            else:
                print(f"yahoo link {link} not work")
        except:
            return 0.0

    def check_word_in_link_with_selenium(self, link, word, threshold=0.001):
        try:
            driver = self.start_driver()
            response = driver.get(link)
            page_content = self.preprocess_text(response.text)
            word = self.preprocess_text(word)
            similarity = self.compute_similarity(page_content, word)
            if similarity >= threshold:
                return link
            driver.quit()
        except:
            return 0.0

    def merge_columns(self, similar_links, search_word, html_filename):
        try:
            df = pd.DataFrame(similar_links)
            required_columns = ['link']
            if not all(column in df.columns for column in required_columns):
                messagebox.showerror("Error", "Missing required columns in the similar links data.")
                return

            df['Result Links'] = df['link']

            html_content = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Search Results</title>
                <!-- Bootstrap CSS -->
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 20px auto;
                        padding: 20px;
                        background-color: #fff;
                        border-radius: 5px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        text-align: center;
                        color: #333;
                    }}
                    .result-button {{
                        color: #fff;
                        background-color: #87CEFA; /* Light blue color */
                        border: none;
                        padding: 10px 20px;
                        margin-bottom: 10px;
                        border-radius: 5px;
                        display: block;
                        text-align: center;
                        text-decoration: none;
                        transition: background-color 0.3s;
                        font-size: 20px; /* Larger font size */
                        font-weight: bold; /* Bold font */
                    }}
                    .result-button:hover {{
                        background-color: #5F9EA0; /* Light blue color on hover */
                    }}
                    .result-button span {{
                        color: black; /* Black color for the site names */
                    }}
                    iframe {{
                        width: 100%;
                        height: 500px;
                        border: none;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Search Results for: {search_word}</h1>
                    {''.join([
                f'<a href="{row["Result Links"]}" target="_blank" class="result-button"><span style="color: black;">{row["Result Links"]}</span></a>' +
                (f'<iframe src="{row["Result Links"]}" title="{row["Result Links"]}"></iframe>' if self.include_iframe_var.get() else '')
                for _, row in df.iterrows() if row["Result Links"]
            ])}
                </div>
                <!-- Bootstrap JS -->
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            '''

            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except Exception as e:
            print("Error", f"An error occurred: {e}")
            messagebox.showinfo("Error", "An error occurred. Please try again.")

    def main(self, file_name_input, folder_path, search_words, links, similarity_threshold):
        try:
            self.start_driver()
            similar_links = []

            for search_word in search_words:
                for link in links:
                    # if 'yahoo' in link:
                    #     similarity = self.check_word_in_link_with_selenium(link, search_word, similarity_threshold)
                    #     if similarity:
                    #         similar_links.append({'link': link})
                    similarity = self.check_word_in_link(link, search_word, similarity_threshold)
                    if similarity:
                        similar_links.append({'link': link})

            now = datetime.datetime.now()
            formatted_now = now.strftime("%Y-%m-%d & %H-%M")
            search_word_safe = search_word.replace(':', '-').replace('"', '')
            max_search_word_length = 30
            truncated_search_word = search_word_safe[:max_search_word_length]

            file_name = f'{truncated_search_word}-{formatted_now}-Search-Data.xlsx'
            excel_path = os.path.join(folder_path, file_name)


            df_all_data = pd.DataFrame(similar_links)
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer_all:
                df_all_data.to_excel(writer_all, index=False, sheet_name='Sheet1')
                worksheet_all = writer_all.sheets['Sheet1']
                worksheet_all.set_column('A:Z', 50)

            html_filename = os.path.join(folder_path, f'Similar-Links-HTML.html')
            self.merge_columns(similar_links, search_word, html_filename)

        except Exception as e:
            print(f"Selenium WebDriver exception: {e}")
            messagebox.showinfo("Error", f"Selenium WebDriver error: {e}")
        except Exception as e:
            print(f"Error occurred: {e}")
            messagebox.showinfo("Error", f"An error occurred: {e}")
        finally:
            if self.driver:
                driver_pid = self.driver.service.process.pid
                self.killDriverZombies(driver_pid)


if __name__ == "__main__":
    app = SearchAboutNews()
    app.mainloop()