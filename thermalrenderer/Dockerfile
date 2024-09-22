FROM python:3

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

STOPSIGNAL SIGINT

COPY . .

CMD [ "python", "-u", "./main.py" ]
