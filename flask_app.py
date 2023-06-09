import os
import logging
from flask import Flask, render_template, request, session
import requests

from dotenv import load_dotenv

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# load .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')



# 파일 경로 설정

def read_text_data():
    data_dict = {}
    file_path = os.path.join(app.root_path, 'area.txt')
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines[1:]:
        line = line.strip().split('\t')
        obs_code = line[0]
        obs_name = line[1]
        data_dict[obs_name] = obs_code

    return data_dict

def get_tide_data(obs_code, date):
    servicekey = os.environ.get('SERVICE_KEY')
    url = f"http://www.khoa.go.kr/api/oceangrid/tideObs/search.do?ServiceKey={servicekey}&ObsCode={obs_code}&Date={date}&ResultType=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        error_message = f"Failed to fetch data. Status code: {response.status_code}"
        app.logger.error(error_message)
        print("Failed to fetch data.")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    obs_dict = read_text_data()
    locations = list(obs_dict.keys())

    date = None
    if request.method == 'POST':

        date = request.form.get('date')
        if date:
            formatted_date = date.replace('-', '')
            sel = request.form.get('location')
            obs_code = obs_dict[sel]
            
            data = get_tide_data(obs_code, formatted_date)
        else:
            return render_template('index.html', error_message="날짜를 선택해주세요.", locations=locations)
        

        if data:
            try:
                name = data['result']['meta']['obs_post_name']
                df = pd.DataFrame(data['result']['data'])
                plot_tide_level(df, name, formatted_date)

                # 현재 선택한 위치, 날짜를 세션에 저장
                session['location'] = sel
                session['date'] = date
                if 'location' in session:
                    default_location = session['location']
                else:
                    default_location = None

                if 'date' in session:
                    default_date = session['date']
                else:
                    default_date = None

                return render_template('index.html', name=name, date=date, formatted_date=formatted_date, default_location=default_location, default_date=default_date, locations=locations)
            except KeyError:

                if 'location' in session:
                    default_location = session['location']
                else:
                    default_location = None

                if 'date' in session:
                    default_date = session['date']
                else:
                    default_date = None
                return render_template('index.html', date=date, error_message="해당 날짜 또는 지역의 데이터는 존재하지 않습니다.", default_location=default_location, default_date=default_date, locations=locations)

    return render_template('index.html', date=date, locations=locations)


# 그래프 이미지 개수를 세고, 이미지가 5개 이상인 경우 가장 오래된 이미지 삭제
def clean_up_images():
    root = os.path.join(app.root_path, 'static')
    image_files = [f for f in os.listdir(root) if f.endswith('_plot.png')]
    if len(image_files) >= 5:
        image_files.sort(key=lambda x: os.path.getmtime(os.path.join(root, x)))
        for i in range(len(image_files) - 4):
            os.remove(os.path.join(root, image_files[i]))



def plot_tide_level(df, name, date):
    # 이미지 파일 경로 생성
    root = os.path.join(app.root_path, 'static')
    filepath = os.path.join(root, f'{name}_{date}_plot.png')
    
    # 이미지 파일이 이미 존재하는지 확인
    if os.path.exists(filepath):
        return

    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rc('font', family='NanumGothic')

    # 날짜 시간 형식 변환
    df['record_time'] = pd.to_datetime(df['record_time'])
    df['tide_level'] = df['tide_level'].astype(int)

    plt.title(f'{name} 조위 그래프')
    plt.plot(df['record_time'], df['tide_level'], marker='o')

    # 축 레이블 및 타이틀 추가
    plt.xlabel('시간')
    plt.ylabel('조위')
    plt.title(f'{name} 조위 그래프')
    # plt.ylim([0,700])
    plt.grid(True)

    # x축 눈금 간격 설정
    plt.xticks(rotation=45)
    plt.gca().yaxis.set_major_locator(plt.MaxNLocator(20))

    # 그래프 저장
    plt.savefig(filepath)

    # 그래프 지우기
    plt.clf()

    # 이미지 정리
    clean_up_images()



if __name__ == '__main__':
    app.run()
