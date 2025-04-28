FROM python:3.10
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /tmp/
WORKDIR /tmp
RUN pip install --no-cache-dir -r requirements.txt
COPY ./database.ini /
COPY ./src/ /src/
WORKDIR /src
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]
#CMD ["/bin/bash"]

