import requests
import json
import os
from datetime import datetime, timedelta
from urllib.request import urlretrieve
from dotenv import load_dotenv

load_dotenv()
recent_day = 7

def login_kidsnote(username, password):
    login_url = 'https://www.kidsnote.com/api/web/login/'
    session = requests.Session()

    session.get(login_url)

    payload = {
        'username': username,
        'password': password,
        'remember_me': 'false'
    }

    session.post(login_url, data=payload)
    return session

def get_my_info(session):
    info_url = 'https://www.kidsnote.com/api/v1/me/info/'
    response = session.get(info_url)
    return json.loads(response.text)

def get_album_list(session, childrens, start_date=None, end_date=None):
    for children in childrens:
        child = children['id']
        child_name = children['name']

        if start_date and end_date:
            search_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            search_end_date = datetime.strptime(end_date, '%Y-%m-%d')
            delta = (search_end_date - search_start_date).days + 1

            for i in range(delta):
                target_date = search_start_date + timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/albums/?page_size=100&tz=Asia%2FSeoul&child={child}&date={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '앨범')

            for i in range(delta):
                target_date = search_start_date + timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/reports/?page_size=100&tz=Asia%2FSeoul&child={child}&date_start={formatted_date}&date_end={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '알림장')
        else:
            today = datetime.now()

            for i in range(int(recent_day)):
                target_date = today - timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/albums/?page_size=100&tz=Asia%2FSeoul&child={child}&date={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '앨범')

            for i in range(int(recent_day)):
                target_date = today - timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')
                response = session.get(f'https://www.kidsnote.com/api/v1_2/children/{child}/reports/?page_size=100&tz=Asia%2FSeoul&child={child}&date_start={formatted_date}&date_end={formatted_date}')
                if response.status_code == 200:
                    albums_info = json.loads(response.text)
                    download_album_images(albums_info, child_name, '알림장')

    return session

def download_album_images(albums_info, child_name, note_type):
    if albums_info['count'] > 0:
        album_list = albums_info['results']
        for album in album_list:
            images = album['attached_images']
            video = album['attached_video']
            if note_type == '알림장':
                title = note_type
            else:
                title = album['title']
            date = album['created'][0:10]

            print(date, title)

            folder_name = f"[{date}]{title}"
            download_dir = os.path.join('download', child_name, folder_name)

            os.makedirs(f"{download_dir}", exist_ok=True)

            # 이미지 URL들 가져오기
            image_urls = [image_json['original'] for image_json in images]
            original_file_names = [image_json['original_file_name'] for image_json in images]

            # 이미지 다운로드
            for i, image_url in enumerate(image_urls):
                filename = f"{date}_{i}_{original_file_names[i]}"
                file_path = os.path.join(download_dir, filename)

                if not os.path.exists(file_path):
                    urlretrieve(image_url, file_path)
                else:
                    print(f"File '{filename}' already exists. Skipping download.")

            # 동영상 다운로드
            if video:
                video_url = video['high']
                original_file_name = video['original_file_name']
                filename = f"{date}_{original_file_name}"
                file_path = os.path.join(download_dir, filename)

                if not os.path.exists(file_path):
                    urlretrieve(video_url, file_path)
                else:
                    print(f"File '{filename}' already exists. Skipping download.")

            if note_type == '알림장':
                with open(os.path.join(download_dir, "content.txt"), "w", encoding="utf-8") as file:
                    file.write(album['content'])

    return

if __name__ == '__main__':
    username = os.getenv('username')
    password = os.getenv('password')
    start_date = os.getenv('start_date')
    end_date = os.getenv('end_date')

    session = login_kidsnote(username, password)
    my_info = get_my_info(session)
    childrens = my_info['children']

    session = get_album_list(session, childrens, start_date, end_date)