FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import torchvision.models as m; m.resnet50(pretrained=True)"

COPY app.py .
COPY imagenet_classes.txt .

EXPOSE 8080

CMD ["python", "app.py"]
