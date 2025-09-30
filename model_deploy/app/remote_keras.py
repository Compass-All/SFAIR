from flask import Flask, request, jsonify
from keras.preprocessing.image import img_to_array
from keras.models import load_model
import numpy as np
import cv2
import cvlib as cv

app = Flask(__name__)

try:
    model = load_model('remote/gender_detection.h5')
except Exception as e:
    print("Error loading model:", e)
    model = None

# Define classes
classes = ['man', 'woman']

@app.route('/predict_remote', methods=['POST'])
def predict_remote():
    try:
        # Get image file from request
        file = request.files['image']

        # Read image file
        image = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_COLOR)
        
        # Detect faces in the image
        faces, confidences = cv.detect_face(image)
        
        
        if len(faces) == 0:
            return jsonify({"error": "No faces detected"}), 400

        # Take the first detected face
        
        face = faces[0]
        
        confidence = confidences[0]
        
        startX, startY, endX, endY = face
        
        # Crop the detected face region
        face_crop = image[startY:endY, startX:endX]
        
        face_crop = cv2.resize(face_crop, (96, 96))
        
        face_crop = face_crop.astype("float") / 255.0
        
        face_crop = img_to_array(face_crop)
        
        face_crop = np.expand_dims(face_crop, axis=0)
        
        # Apply gender detection on face if model is loaded
        if model is not None:
            conf = model.predict(face_crop)[0]
            return jsonify(conf.tolist())
        else:
            return jsonify({"error": "Model not loaded"}), 500  # Internal Server Error

    except Exception as e:
        return jsonify({"error": str(e)}), 400  # Bad Request

if __name__ == '__main__':
    app.run(port=5001, debug=True)
