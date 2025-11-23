from typing import Dict, List, TYPE_CHECKING     
if TYPE_CHECKING:
    from ultralytics.engine.results import Results
from PIL import Image
import io
import cv2
import numpy as np
import random


def save_predictions(predictions: Dict[str, "Results"]) -> List[io.BytesIO]:
    """
    Saves YOLO predictions to in-memory buffers instead of disk.
    Returns a list of BytesIO objects (image buffers).
    """
    buffers = []

    for i, (prompt, result) in enumerate(predictions.items()):
        # Get the plotted result as a NumPy array (HWC)
        image_array = result.plot()

        # Convert to PIL Image
        image = Image.fromarray(image_array)

        # Save to BytesIO buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        buffers.append(buffer)

    return buffers


def annotate_image(image, prompt_to_prob):

    image_np = np.array(image) 
    frame_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    y_offset = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.45
    thickness = 2
    colour = (0, 0, 0)

    sorted_prompt_to_prob = dict(sorted(prompt_to_prob.items(), key = lambda item:-item[1]))

    for prompt, prob in sorted_prompt_to_prob.items():
        prefix = "A road scene where a "
        suffix = " is visible"

        # Strip prefix and suffix if they exist
        if prompt.startswith(prefix):
            prompt = prompt[len(prefix):]
        if prompt.endswith(suffix):
            prompt = prompt[:-len(suffix)]

        text = f"{prompt} ({prob:.2f})"

        cv2.putText(frame_bgr, text, (10, y_offset), font, font_scale, colour, thickness)
        y_offset += 30
    
    # Encode the annotated image as JPEG
    success, encoded_image = cv2.imencode('.jpg', frame_bgr)
    if not success:
        raise ValueError("Image encoding failed")

    # Convert to BytesIO buffer
    buffer = io.BytesIO(encoded_image.tobytes())
    buffer.seek(0)

    return buffer 


def save_combined_result(image):
    """
    Saves YOLO predictions to in-memory buffers instead of disk.
    Returns a list of BytesIO objects (image buffers).
    """
    result_img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result_pil = Image.fromarray(result_img_rgb)

    # Save image to a BytesIO buffer
    img_io = io.BytesIO()
    result_pil.save(img_io, format='JPEG') 
    img_io.seek(0)

    return img_io
 

def draw_combined_predictions(predictions, image):
    # Convert PIL to OpenCV format (RGB → BGR)
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    label_colors = {}

    for model_name, result in predictions.items():
        if not result or len(result) == 0:
            continue

        boxes = result[0].boxes
        names = result[0].names

        for box in boxes:
            cls_id = int(box.cls)
            label = names[cls_id]
            conf = float(box.conf)  # confidence score
            
            """
            if label not in label_colors:
                label_colors[label] = tuple(random.randint(0, 255) for _ in range(3))
            """
            color = (0, 0 ,0)

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Format: label: 0.92
            label_text = f"{label}: {conf:.2f}"
            print(f"{label_text}, box: {(x1, y1), (x2, y2)}")

            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 4)

    return image

def extract_combined_predictions(predictions):
    results = []

    for model_name, result in predictions.items():
        if not result or len(result) == 0:
            continue

        boxes = result[0].boxes
        names = result[0].names

        for box in boxes:
            cls_id = int(box.cls)
            label = names[cls_id]
            conf = float(box.conf)

            label_text = f"{label}: {conf:.2f}"
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            results.append({
                "label": label,
                "confidence": conf,
                "text": label_text,
                "box": (x1, y1, x2, y2)
            })

    return results

