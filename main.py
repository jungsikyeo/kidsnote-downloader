import os
import requests
import time
import json
from urllib.request import urlretrieve
from selenium import webdriver
from pathlib import Path
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from dotenv import load_dotenv
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

recent_day = 7

env_path = Path(os.path.abspath(os.path.dirname(__file__))) / ".env"
load_dotenv(dotenv_path=env_path)

def login(username, password):

    os.environ['WDM_LOG_LEVEL'] = '0'  # 이 부분을 추가합니다.
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(executable_path=ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install(), chrome_options=options)
    driver.get('https://www.kidsnote.com/login')

    username_input = driver.find_element(By.NAME, 'username')
    password_input = driver.find_element(By.NAME, 'password')

    username_input.send_keys(username)
    password_input.send_keys(password)

    login_button = driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/main/div/form/button')
    login_button.click()

    time.sleep(3)

    return driver

def get_user_info(driver):
    cookies = driver.get_cookies()
    session = requests.Session()
    
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    
    response = session.get('https://www.kidsnote.com/api/v1/me/info/')
    
    if response.status_code == 200:
        user_info = json.loads(response.text)
        return user_info
    else:
        print(f"Error: {response.status_code}")
        return None
    
def download_album_images(albums_info):
    if albums_info['count'] > 0:
        album_list = albums_info['results']
        for album in album_list:
            images = album['attached_images']
            video = album['attached_video']
            title = album['title']
            date = album['created'][0:10]

            print(date, title)

            folder_name = f"[{date}]{title}"
            download_dir = os.path.join(session['download_folder'], folder_name)

            os.makedirs(f"{download_dir}", exist_ok=True)

            # 이미지 URL들 가져오기
            image_urls = [image_json['original'] for image_json in images]
            original_file_names = [image_json['original_file_name'] for image_json in images]

            # 이미지 다운로드
            for i, image_url in enumerate(image_urls, start=0):
                filename = f"{date}_{i}_{original_file_names[i]}"
                file_path = os.path.join(download_dir, filename)
                
                if not os.path.exists(file_path):
                    urlretrieve(image_url, file_path)
                else:
                    print(f"File '{filename}' already exists. Skipping download.")

    return 

def get_album_list(driver, childrens, start_date=None, end_date=None):
    cookies = driver.get_cookies()
    session = requests.Session()
    
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    for children in childrens:
        child = children['id']

        if start_date and end_date:
            search_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            search_end_date = datetime.strptime(end_date, '%Y-%m-%d')
            delta = (search_end_date - search_start_date).days + 1

            for i in range(delta):
                target_date = search_start_date + timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/albums/?page_size=12&tz=Asia%2FSeoul&child={child}&date={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info)
        else:
            today = datetime.now()

            for i in range(int(recent_day)):
                target_date = today - timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/albums/?page_size=12&tz=Asia%2FSeoul&child={child}&date={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info)                

    return driver


def main():
    print('main!')

# Add this route to serve the HTML file containing the folder picker
@app.route('/')
def index():
    return render_template('index.html')

# Add this route to handle the selected folder and credentials
@app.route('/set-download-folder', methods=['POST'])
def set_download_folder():
    try:
        data = request.json
        folder = data.get('folder')
        username = data.get('username')
        password = data.get('password')

        session['download_folder'] = folder
        session['username'] = username
        session['password'] = password

        print("Data received: ", data)

        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

# Update the start-download route to use the stored credentials
@app.route('/start-download', methods=['POST'])
def start_download():
    try:
        data = request.json
        folder = data.get('folder')
        username = data.get('username')
        password = data.get('password')
        start_date = data.get('startDate')
        end_date = data.get('endDate')

        session['download_folder'] = folder
        session['username'] = username
        session['password'] = password

        driver = login(username, password)

        user_info = get_user_info(driver)
        childrens = user_info['children']

        driver = get_album_list(driver, childrens, start_date, end_date)

        driver.quit()

        return jsonify({'success': True})
    except:
        return jsonify({'success': False})