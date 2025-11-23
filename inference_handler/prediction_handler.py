import torch
import torch.nn.functional as F
import json
import os
from PIL import Image
import numpy as np
from scipy.stats import mode
import time
time_taken_list = []


def return_top_prompts(image, prompt_list, prompt_to_model_dict, clip_model, clip_processor, verbose):

    #total_count = len(prompt_list)
    #print(f"total classes: {total_count}")
 
    image_np = np.array(image)
    highlight_fixed = suppress_highlights(image_np, threshold=200)

    final_image = Image.fromarray(highlight_fixed)
    inputs = clip_processor(text = prompt_list, images = final_image, return_tensors="pt", padding=True)
    prompt_to_prob_dict = {}

    with torch.no_grad():
        outputs = clip_model(**inputs)
        
        # Get raw image/text features
        image_features = outputs.image_embeds  # [1, hidden_dim]
        text_features = outputs.text_embeds    # [num_classes, hidden_dim]
        
        # Normalize features
        image_features = F.normalize(image_features, p=2, dim=-1)
        text_features = F.normalize(text_features, p=2, dim=-1)
        
        # Cosine similarities
        sims = image_features @ text_features.T  # [1, num_classes]

        if len(prompt_list) == 1:
            prob = torch.sigmoid(sims[0])  
            return {prompt_list[0]: prob.item()}
        
        # Z-score normalization
        sims_norm = (sims - sims.mean()) / sims.std()

        # Apply sigmoid
        probs = torch.sigmoid(sims_norm)[0]   # [num_classes]
        
    # Keep anything above average OR reasonably close to top
    sig_z = (sims_norm[0] > 0.2)
    sig_val = (probs >= 0.8 * probs.max())
    significant_indices = (sig_z | sig_val).nonzero(as_tuple=True)[0]
    count = 0
    
    if (verbose):
        # Print class-wise percentages
        for clss, prob in zip(prompt_list, probs):
            print(f"{clss:<35}: {prob.item():.3f}")
    
    # Print only significant predictions
    if (verbose):
        print("Significantly strong predictions:\n")
    for idx in significant_indices:
        count += 1
        clss = prompt_list[idx]
        prob = probs[idx]
        prompt_to_prob_dict[clss] = prob
        if (verbose):
            print(f"{clss} -> {prob}")

    #print(f"Total Count Significant classes: {count}")
    sorted_prompt_to_prob = dict(sorted(prompt_to_prob_dict.items(), key=lambda item: -item[1]))
    return sorted_prompt_to_prob


# Function to return the models to run for the image:
def models_to_run(prompt_to_prob_dict, prompt_to_model_dict):

    return list({ prompt_to_model_dict[prompt] for prompt in prompt_to_prob_dict if prompt in prompt_to_model_dict })


# Function to return a list of model names given the model:
def model_name_list(model_list, name_to_model_dict):
    model_names = []
    for model in model_list:
        for name, model_2 in name_to_model_dict.items():
            if model == model_2:
                model_names.append(name)
    print(model_names)
    return model_names


def run_best_yolo_models(image, models, top_model_names, confidence):

    predictions = {}
    for name in top_model_names:
        model = models[name]
        results = model.predict(source = image, conf = confidence, verbose = True)

        if results:
            predictions[name] = results[0]
    return predictions


def suppress_highlights(image, threshold=240):
    """
    Caps overly bright pixel values to suppress highlights (like headlights).
    - image: RGB image as a NumPy array
    - threshold: max brightness per channel (0-255)
    """
    return np.minimum(image, threshold).astype(np.uint8)


def summary_statistics(prompt_to_model_dict, clip_model, clip_processor):
    with open('dataset/labels/labels_new.json', 'r') as file:
        data = json.load(file)
    
    image_dir = 'dataset/reference_images/'
    
    prompts = ["a street light", "an animal", "Pot Hole in road", "Crack on Road", "Broken Pavement", 
               "Fallen Tree blocking road", "Fallen Electric Pole blocking road", 
               "Traffic Light", "Traffic Cone", "bike", 
               "car", "Bus", "Jeep", "Truck", "Cycle", "Pedestrian", 
               "painted traffic line", "Hanging Power Line", "Broken Divider",] 

    prompt_list = [f"A road scene where {prompt} is visible" for prompt in prompts]
  
    extra_count_array = np.array([])
    count = 0
    
    missed_model_dict = {prompt:0 for prompt in prompts}

    for path, folder, files in os.walk(image_dir):

        for filename in files: 
            start_time = time.time()

            count+= 1
            predicted_labels = []
            ground_truth_labels = []
            image_file = os.path.join(image_dir, filename)
            image = Image.open(image_file).convert("RGB")

            prompt_to_label_dict = {prompt:label for prompt, label in zip(prompt_list, prompts)}

            image_np = np.array(image)

            highlight_fixed = suppress_highlights(image_np, threshold=194)
        
            final_image = Image.fromarray(highlight_fixed)
            
            prompt_to_prob_dict = return_top_prompts(final_image, prompt_list, prompt_to_model_dict, clip_model, clip_processor, False)

            for prompt, prob in prompt_to_prob_dict.items():
                if prompt in prompt_to_label_dict:
                    predicted_labels.append((prompt_to_label_dict[prompt], prob))

            for image_dict in data:
                if image_dict["file"] == filename:
                    ground_truth_labels = image_dict["labels"]

            actual_count = len(ground_truth_labels)
        
            extra_count = 0
            for label, prob in predicted_labels:
                if label not in ground_truth_labels:
                    extra_count += 1

            print(f"\nimage -> {filename}")
            print(f"Actual Label -> {ground_truth_labels}")
            print(f"Predicted Label:")

            for label, prob in sorted(predicted_labels, key = lambda x:-x[1]):
                print(f"{label} -> {prob:.4}")

            predicted_label_names = [label for label, _ in predicted_labels]

            for label in ground_truth_labels:
                if label not in predicted_label_names:
                    missed_model_dict[label] += 1
                    print(f"Missed Label -> {label}")

            print("\n")
            extra_count_array = np.append(extra_count_array, extra_count)
            print(f"Actual Count: {actual_count}, Extra Models: {extra_count}")

            elapsed_time = time.time() - start_time
            print(f"Time taken: {elapsed_time:.2f} seconds")
            time_taken_list.append(elapsed_time)

    print("-----------------------------\n")
    print("Final Summary:\n")
    print("No. of Images checked:", count)
    print(f"Average Extra Models (Mean): {extra_count_array.mean()}")
    print(f"Max Extra Models: {extra_count_array.max()}")
    print(f"Min Extra Models: {extra_count_array.min()}")
    print(f"Mode Extra Models: {mode(extra_count_array).mode}, frequency: {mode(extra_count_array).count}\n")
    #print(extra_count_array)
    freq_dict = {}
    for freq in extra_count_array:
        freq_dict[freq] = 0

    for freq in extra_count_array:
        freq_dict[freq] += 1
    
    for freq, count in freq_dict.items():
        print(f"{freq} --> {count}")
    
    print(f"No. of times models missed:\n")

    missed_model_dict = dict(sorted(missed_model_dict.items(), key = lambda x:x[1]))
    for model, freq in missed_model_dict.items():
        if freq > 0:
            print(f"{model} --> {freq}")
    
    print(f"\nTime Summary:")
    print(f"Average Time per Image: {np.mean(time_taken_list):.2f} seconds")
    print(f"Max Time: {np.max(time_taken_list):.2f} seconds")
    print(f"Min Time: {np.min(time_taken_list):.2f} seconds")


def run_best_yolo_models(image, models, top_model_names, confidence):

    predictions = {}
    for name in top_model_names:
        model = models[name]
        results = model.predict(source = image, conf = confidence, verbose = True)

        if results:
            predictions[name] = results[0]
    
    return predictions