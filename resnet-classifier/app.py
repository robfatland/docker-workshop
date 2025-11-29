from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import torch
from torchvision import models, transforms
import io

app = Flask(__name__)

# Load pretrained ResNet50
model = models.resnet50(pretrained=True)
model.eval()

# ImageNet preprocessing
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Load ImageNet labels
with open('imagenet_classes.txt') as f:
    labels = [line.strip() for line in f.readlines()]

HTML = '''
<!DOCTYPE html>
<html>
<head><title>ResNet Image Classifier</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto;">
    <h1>ResNet-50 Image Classifier</h1>
    <form action="/predict" method="post" enctype="multipart/form-data">
        <input type="file" name="image" accept="image/*" required>
        <button type="submit">Classify Image</button>
    </form>
    <div id="result"></div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    img = Image.open(io.BytesIO(file.read())).convert('RGB')
    
    # Preprocess and predict
    img_tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        output = model(img_tensor)
    
    # Get top 5 predictions
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    top5_prob, top5_idx = torch.topk(probabilities, 5)
    
    results = [
        {'class': labels[idx], 'probability': f'{prob.item()*100:.2f}%'}
        for prob, idx in zip(top5_prob, top5_idx)
    ]
    
    return jsonify({'predictions': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
