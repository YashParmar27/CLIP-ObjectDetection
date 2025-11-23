from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from inference_handler.input_handler import prepare_image_from_bytes, prepare_image_from_base64
from inference_handler.model_loader import load_models, load_clip_model, update_config_yaml
from inference_handler.output_handler import annotate_image, extract_combined_predictions
from inference_handler.prediction_handler import return_top_prompts, suppress_highlights, model_name_list, models_to_run, run_best_yolo_models
from utils.config_loader import load_config
import os
import cv2
from PIL import Image
import numpy as np
import tempfile
import base64
import torch
import json
from flask_socketio import SocketIO


config = load_config()

model_paths = config["models"]
text_prompt_list = config["text_prompts"]
output = config["output"]

from flask_cors import CORS
app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# Pre-load once during startup:
models = load_models(model_paths)
clip_model, processor = load_clip_model()

prompt_to_model_dict = {
    # Human face
    "A photo of a person's face": models["face_detection"],
}

@socketio.on('frame')
def handle_frame(data):
    if not data["image"]:
        return jsonify({"error": "No image received!"})
    
    img_base64 = data["image"]
    image = prepare_image_from_base64(img_base64)

    if data["prompts"]:
        prompt_list = data["prompts"]
        image_np = np.array(image)

        highlight_fixed = suppress_highlights(image_np, threshold=194)
            
        final_image = Image.fromarray(highlight_fixed)

        prompt_to_prob_dict = return_top_prompts(final_image, prompt_list, prompt_to_model_dict, clip_model, processor, True)

        prompt_to_prob_dict = tensor_to_json_serializable(prompt_to_prob_dict)
        
        socketio.emit("prediction", {
            "type": "clip",
            "data": prompt_to_prob_dict
        })

        return jsonify({"status": "frame received"}) 
    else:
        prompt_list = [
        ]
        
        image_np = np.array(image)

        highlight_fixed = suppress_highlights(image_np, threshold=194)
            
        final_image = Image.fromarray(highlight_fixed)

        prompt_to_prob_dict = return_top_prompts(final_image, prompt_list, prompt_to_model_dict, clip_model, processor, True)

        models_list = models_to_run(prompt_to_prob_dict, prompt_to_model_dict)
        model_names = model_name_list(models_list, models)

        predictions = run_best_yolo_models(image, models, model_names, output["confidence"])
        result_dict = extract_combined_predictions(predictions)

        socketio.emit("prediction", {
            "type": "yolo",
            "data": result_dict
        })

        return jsonify({"status": "frame received"})



@app.route('/predict', methods = ["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded!"}), 400 # HTTP status-code for a bad request
    
    file = request.files["image"]
    prompts = request.form.get("prompts")

    if prompts and json.loads(prompts) != [] and json.loads(prompts) != ['']:
        prompt_list = json.loads(prompts)
        image = prepare_image_from_bytes(file)
        image_np = np.array(image)

        highlight_fixed = suppress_highlights(image_np, threshold=194)
            
        final_image = Image.fromarray(highlight_fixed)
        print("Prompt list:", prompt_list)
        print("Image type:", type(final_image))

        prompt_to_prob_dict = return_top_prompts(final_image, prompt_list, prompt_to_model_dict, clip_model, processor, True)

        prompt_to_prob_dict = tensor_to_json_serializable(prompt_to_prob_dict)
        print(prompt_to_prob_dict)
        socketio.emit("prediction", {
            "type": "clip",
            "data": prompt_to_prob_dict
        })

        return jsonify({"status": "frame received"})

    else:
       
        prompt_list = [
            "A photo of a person's face",
        ]

        image = prepare_image_from_bytes(file)
        image_np = np.array(image)

        highlight_fixed = suppress_highlights(image_np, threshold=194)
            
        final_image = Image.fromarray(highlight_fixed)

        prompt_to_prob_dict = return_top_prompts(final_image, prompt_list, prompt_to_model_dict, clip_model, processor, True)

        models_list = models_to_run(prompt_to_prob_dict, prompt_to_model_dict)
        model_names = model_name_list(models_list, models)

        predictions = run_best_yolo_models(image, models, model_names, output["confidence"])

        result_dict = extract_combined_predictions(predictions)
        
        socketio.emit("prediction", {
            "type": "yolo",
            "data": result_dict
        })

        return jsonify({"status": "frame received"})
 

# Predicting only with prompts:
@app.route('/predict_image', methods = ["POST"])
def predict_image():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded!"}), 400 
    
    file = request.files["image"]
    prompts = request.form.get("prompts")


    if json.loads(prompts) != [] and json.loads(prompts) != ['']:
        prompt_list = json.loads(prompts)
        image = prepare_image_from_bytes(file)
        image_np = np.array(image)

        highlight_fixed = suppress_highlights(image_np, threshold=194)
            
        final_image = Image.fromarray(highlight_fixed)

        prompt_to_prob_dict = return_top_prompts(final_image, prompt_list, prompt_to_model_dict, clip_model, processor, True)

        buffer = annotate_image(image, prompt_to_prob_dict)
        img_bytes = buffer.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        prompt_to_prob_dict = tensor_to_json_serializable(prompt_to_prob_dict)
        return jsonify({
            "mediaType": "image",
            "image": img_base64,
            "prediction": prompt_to_prob_dict
            })

    else:
        return jsonify({"error": "No Prompts Given!"})


def tensor_to_json_serializable(d):
    return {k: (v.item() if torch.is_tensor(v) else v) for k, v in d.items()}


@app.route('/predict_video', methods=["POST"])
def predict_video():
    if "video" not in request.files:
        return jsonify({"Error": "Video not uploaded!"}), 400

    video_file = request.files["video"]
    prompts = request.form.get("prompts")
    print(json.loads(prompts))

    if json.loads(prompts) != [] and json.loads(prompts) != ['']:
        prompt_list = json.loads(prompts)
    else:
        prompt_list = [
            "A photo of a person's face",
        ]

    # Save uploaded video to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
        temp.write(video_file.read())
        video_path = temp.name

    # Extract frames using the saved path
    video_frames = extract_frames(video_path, frame_interval=30)
    if not video_frames:
        return jsonify({"Error": "No frames extracted from video!"}), 400

    annotated_frames = []

    for frame in video_frames:
        frame_np = np.array(frame)
        highlight_fixed = suppress_highlights(frame_np, 194)
        final_image = Image.fromarray(highlight_fixed)

        prompt_to_prob_dict = return_top_prompts(
            final_image, prompt_list, prompt_to_model_dict,
            clip_model, processor, True
        )
        annotated_frame = annotate_frame(frame_np, prompt_to_prob_dict)
        annotated_frames.append(annotated_frame)
    
    height, width, _ = annotated_frames[0].shape
    fps = 10  

    output_path = tempfile.mktemp(suffix=".mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame in annotated_frames:
        out.write(frame)
    out.release()

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return jsonify({"Error": "Video processing failed."}), 500

    with open(output_path, "rb") as f:
        video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

    os.remove(output_path)

    return jsonify({
        "mediaType": "video",
        "video": video_base64
    })
    

@app.route('/add_model', methods = ["POST"])
def add_model():
   
    model_file = request.files["model"]
    model_name = request.form.get("name")
    model_prompt = request.form.getlist("prompt")

    if not model_file or not model_name or not model_prompt:
        return jsonify({"error": "Missing model file or model name or model prompt"}), 400

    save_path = os.path.join("models", f"{model_name}_best.pt")
    model_file.save(save_path)

    update_config_yaml(model_name, model_prompt)

    return jsonify({"message": f"Model '{model_name}' registered successfully!"}), 200


def extract_frames(video_path, frame_interval = 30):
    vidcap = cv2.VideoCapture(video_path)
    frames = []

    success, image = vidcap.read()
    count = 0

    while success:
        if count % frame_interval == 0:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            frames.append(image)

        success, image = vidcap.read()
        count += 1
    
    vidcap.release()
    return frames


def annotate_frame(frame, prompt_to_prob):
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    y_offset = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    colour = (0, 0, 0)

    sorted_prompt_to_prob = dict(sorted(prompt_to_prob.items(), key=lambda item: -item[1]))

    for prompt, prob in sorted_prompt_to_prob.items():
        text = f"{prompt} ({prob:.2f})"
        cv2.putText(frame_bgr, text, (10, y_offset), font, font_scale, colour, thickness)
        y_offset += 30
    
    return frame_bgr

if __name__ == '__main__':
    socketio.run(app, debug=True)
