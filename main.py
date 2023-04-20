import time
import re
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.request import urlretrieve
from dotenv import load_dotenv

load_dotenv()
recent_day = 7

def log(message):
    if message:
        sys.stdout.write(json.dumps({'type': 'log', 'message': message}, ensure_ascii=False) + '\n')
        sys.stdout.flush()

def download_complete(message):
    if message:
        sys.stdout.write(json.dumps({'type': 'download-complete', 'message': message}, ensure_ascii=False) + '\n')
        sys.stdout.flush()

def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    return sanitized_filename

def login_kidsnote(session, username, password):
    login_url = 'https://www.kidsnote.com/api/web/login/'

    session.get(login_url)

    payload = {
        'username': username,
        'password': password,
        'remember_me': 'false'
    }

    response = session.post(login_url, data=payload)

    if response.status_code == 200:
        log("Login successful")
    else:
        log(f"Login failed with status code: {response.status_code}")

    return session

def get_my_info(session):
    info_url = 'https://www.kidsnote.com/api/v1/me/info/'
    response = session.get(info_url)
    response_text = json.loads(response.text)
    return response_text


def get_album_list(session, childrens, start_date=None, end_date=None, download_folder='download'):
    for children in childrens:
        child = children['id']
        child_name = children['name']

        log(f"{child_name} download start..")

        if start_date and end_date:
            search_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            search_end_date = datetime.strptime(end_date, '%Y-%m-%d')
            delta = (search_end_date - search_start_date).days + 1

            for i in range(delta):
                target_date = search_start_date + timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/albums/?page_size=1500&tz=Asia%2FSeoul&child={child}&date={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '앨범', download_folder)

            for i in range(delta):
                target_date = search_start_date + timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/reports/?page_size=1500&tz=Asia%2FSeoul&child={child}&date_start={formatted_date}&date_end={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '알림장', download_folder)
        else:
            today = datetime.now()

            for i in range(int(recent_day)):
                target_date = today - timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/albums/?page_size=1500&tz=Asia%2FSeoul&child={child}&date={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '앨범', download_folder)

            for i in range(int(recent_day)):
                target_date = today - timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/reports/?page_size=1500&tz=Asia%2FSeoul&child={child}&date_start={formatted_date}&date_end={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '알림장', download_folder)

    return session

def download_album_images(albums_info, child_name, note_type, download_folder):
    if albums_info['count'] > 0:
        return_log = ""
        album_list = albums_info['results']
        for album in album_list:
            images = album['attached_images']
            video = album['attached_video']
            if note_type == '알림장':
                title = note_type
            else:
                title = album['title']
            date = album['created'][0:10]

            folder_name = f"[{date}]{title}"
            sanitized_folder_name = sanitize_filename(folder_name)
            download_dir = os.path.join(download_folder, child_name, sanitized_folder_name)

            os.makedirs(download_dir, exist_ok=True)

            # 이미지 URL들 가져오기
            image_urls = [image_json['original'] for image_json in images]
            original_file_names = [image_json['original_file_name'] for image_json in images]

            # 이미지 다운로드
            for i, image_url in enumerate(image_urls):
                filename = f"{date}_{i}_{original_file_names[i]}"
                file_path = os.path.join(download_dir, filename)

                if not os.path.exists(file_path):
                    log(f"Downloading {filename} ...")
                    urlretrieve(image_url, file_path)
                    log(f"{filename} download complete.")
                else:
                    log(f"File {filename} already exists. Skipping download.")
                    time.sleep(0.05)

            # 동영상 다운로드
            if video:
                video_url = video['high']
                original_file_name = video['original_file_name']
                filename = f"{date}_{original_file_name}"
                file_path = os.path.join(download_dir, filename)

                if not os.path.exists(file_path):
                    log(f"Downloading {filename} ...")
                    urlretrieve(video_url, file_path)
                    log(f"{filename} download complete.")
                else:
                    log(f"File {filename} already exists. Skipping download.")
                    time.sleep(0.05)

            if note_type == '알림장':
                with open(os.path.join(download_dir, "content.txt"), "w", encoding="utf-8") as file:
                    file.write(album['content'])
                    log(f"{date} {note_type} download complete.")

    return return_log

if __name__ == '__main__':
    username = sys.argv[1]
    password = sys.argv[2]
    start_date = sys.argv[3] if len(sys.argv) > 3 else None
    end_date = sys.argv[4] if len(sys.argv) > 4 else None
    download_folder = sys.argv[5] if len(sys.argv) > 5 else 'download'

    session = requests.Session()
    session = login_kidsnote(session, username, password)
    my_info = get_my_info(session)
    childrens = my_info['children']

    session = get_album_list(session, childrens, start_date, end_date, download_folder)

    download_complete("All download end.")