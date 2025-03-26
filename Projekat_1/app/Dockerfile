FROM python:3.12.3

WORKDIR /home/milan/Desktop/rag_test/Projekat_1

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]