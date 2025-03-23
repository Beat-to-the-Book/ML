# Python 3.9 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Flask 애플리케이션 복사
COPY app app
COPY run.py .

# 실행 명령어
CMD ["python", "run.py"]
