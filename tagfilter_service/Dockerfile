FROM python:3.11-slim

WORKDIR /app

COPY common ./common
COPY tagfilter_service/ .

RUN apt-get update && apt-get install -y gcc

COPY tagfilter_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

COPY tagfilter_service/models/nltk_data /usr/share/nltk_data
ENV NLTK_DATA=/usr/share/nltk_data

EXPOSE 5000

CMD ["python", "app.py"]