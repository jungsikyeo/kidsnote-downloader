from multiprocessing import Process
import main  # 기존의 main.py 파일을 임포트

app = main.app  # main에서 Flask app 객체를 가져옵니다.

def run_flask():
    app.run()

if __name__ == '__main__':
    # Flask 서버를 별도의 프로세스로 실행
    flask_process = Process(target=run_flask)
    flask_process.start()

    # 일렉트론 앱 실행
    main.main()

    # 일렉트론 앱이 종료되면 Flask 프로세스도 종료
    flask_process.join()
