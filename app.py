import os
from flask import Flask, render_template, request, session
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 파일 경로 설정

def read_text_data():
    data_dict = {}
    file_path = os.path.join(os.path.dirname(__file__), 'area.txt')
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines[1:]:
        line = line.strip().split('\t')
        obs_code = line[0]
        obs_name = line[1]
        data_dict[obs_name] = obs_code

    return data_dict

def get_tide_data(obs_code, date):
    url = f"http://www.khoa.go.kr/api/oceangrid/tideObs/search.do?ServiceKey=xnh8xBLZBTnx01kAkLbzbA==&ObsCode={obs_code}&Date={date}&ResultType=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to fetch data.")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    obs_dict = read_text_data()
    locations = list(obs_dict.keys())
    
    if request.method == 'POST':
        
        sel = request.form.get('location')
        date = "20230506"
        obs_code = obs_dict[sel]
        
        data = get_tide_data(obs_code, date)
        

        if data is not None:
            try:
                name = data['result']['meta']['obs_post_name']
                df = pd.DataFrame(data['result']['data'])
                plot_tide_level(df, name, date)

                # 현재 선택한 위치를 세션에 저장
                session['location'] = sel
                if 'location' in session:
                    default_location = session['location']
                else:
                    default_location = None

                
                return render_template('index.html', name=name, date=date, default_location=default_location, locations=locations)
            except KeyError:
                if 'location' in session:
                    default_location = session['location']
                else:
                    default_location = None
                return render_template('index.html', error_message="해당 데이터는 존재하지 않습니다.", default_location=default_location, locations=locations)

    return render_template('index.html', locations=locations)

def plot_tide_level(df, name, date):
    # 이미지 파일 경로 생성
    filepath = os.path.join('static', f'{name}_{date}_plot.png')
    
    # 이미지 파일이 이미 존재하는지 확인
    if os.path.exists(filepath):
        return

    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rc('font', family='NanumGothic')

    # 날짜 시간 형식 변환
    df['record_time'] = pd.to_datetime(df['record_time'])
    df['tide_level'] = df['tide_level'].astype(int)

    plt.title(f'{name} Tide Level Graph')
    plt.plot(df['record_time'], df['tide_level'], marker='o')

    # 축 레이블 및 타이틀 추가
    plt.xlabel('Record Time')
    plt.ylabel('Tide Level')
    plt.title(f'{name} Tide Level Graph')

    # x축 눈금 간격 설정
    plt.xticks(rotation=45)
    plt.gca().yaxis.set_major_locator(plt.MaxNLocator(20))

    # 그래프 저장
    plt.savefig(filepath)

    # 그래프 지우기
    plt.clf()



if __name__ == '__main__':
    app.run()
