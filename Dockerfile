FROM python:3.9.1
ADD . /task_api
WORKDIR /task_api
COPY ./requirements.txt ./task_api/requirements.txt

RUN pip install -r requirements.txt
COPY . /task_api

CMD ["pyhton", "-m", "main.py"]