from flask import Flask, request, jsonify, render_template_string
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
import io

app = Flask(__name__)

# Load Hugging Face ResNet-50 model
processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
model = AutoModelForImageClassification.from_pretrained("microsoft/resnet-50")
model.eval()

HTML = '''
<!DOCTYPE html>
<html>
<head><title>ResNet Image Classifier</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto;">
    <h1>ResNet-50 Image Classifier</h1>
    <p>Powered by Hugging Face 🤗</p>
    <form action="/predict" method="post" enctype="multipart/form-data">
        <input type="file" name="image" accept="image/*" required>
        <button type="submit">Classify Image</button>
    </form>
</body>
</html>
'''

RESULTS_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Classification Results</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto;">
    <h1>Classification Results</h1>
    <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f0f0f0;">
            <th>Class</th>
            <th>Probability</th>
        </tr>
        {% for pred in predictions %}
        <tr>
            <td>{{ pred.class }}</td>
            <td>{{ pred.probability }}</td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="/"><button style="padding: 10px 20px; font-size: 16px;">Try Again</button></a>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return "No image uploaded", 400
    
    file = request.files['image']
    img = Image.open(io.BytesIO(file.read())).convert('RGB')
    
    # Process image and get predictions using Hugging Face
    inputs = processor(img, return_tensors="pt")
    outputs = model(**inputs)
    
    # Get top 5 predictions
    probs = outputs.logits.softmax(dim=1)[0]
    top5_prob, top5_idx = probs.topk(5)
    
    results = [
        {'class': model.config.id2label[idx.item()], 'probability': f'{prob.item()*100:.2f}%'}
        for prob, idx in zip(top5_prob, top5_idx)
    ]
    
    return render_template_string(RESULTS_HTML, predictions=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

