from typing import Dict, List, Tuple, cast, TYPE_CHECKING
from ultralytics import YOLO    
from transformers import CLIPModel, CLIPProcessor
import re
import yaml


def update_config_yaml(model_name, text_prompts, config_path="utils/config.yaml"):

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    config['models'][model_name] = f"models/{model_name}_best.pt"
    config['text_prompts'][model_name] = text_prompts

    with open(config_path, 'w') as f:
        yaml.dump(config, f)


def get_class(model_class_dict):
    class_list = []
    for classes in model_class_dict.values():
        for name in classes:
            class_list.append(name)
    return class_list


def load_models(model_paths: Dict[str, str]) -> Dict[str, YOLO]:
    """
    Usage: Load pre-trained YOLO models for object detection.
    Outputs: Dictionary of YOLO models keyed by their names.
    """
    return {name: YOLO(path) for name, path in model_paths.items()}


def load_clip_model() -> Tuple[CLIPModel, CLIPProcessor]:
    """
    Usage: Returns the CLIP model and processor.
    Input: None
    Outputs: A Tuple of the clip model and processor
    
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = cast(CLIPProcessor, CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32"))
    """
    clip_model = CLIPModel.from_pretrained("wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M")
    processor = cast(CLIPProcessor, CLIPProcessor.from_pretrained("wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M"))

    return clip_model, processor


def clean_labels(label_list: List[str]) -> List[str]:
    """
    Usage: Clean the labels by replacing underscores and hyphens with spaces,
    converting to title case, and removing digits.
    Inputs: List of labels (strings)
    Outputs: List of cleaned labels (strings).
    """

    cleaned_label_list = []
    for label in label_list:
        label = label.replace("_", " ").replace("-", " ")
        label = label.title()
        label = re.sub(r'\d+', '', label).strip()
        cleaned_label_list.append(label)
    return cleaned_label_list


def get_text_prompts(models: Dict[str, YOLO], input_text_dict: Dict[str, str], text_to_model_dict: Dict[str, YOLO]):
    """
    Usage: Get text-prompts for CLIP using the YOLO model labels.
    This function generates text prompts by prepending a base input text to each label from the YOLO model.
    Inputs:
    - model: The YOLO model to be used for object detection.
    - input_text: The base text to prepend to each label.
    - text_prompts: A dictionary to store the generated text prompts with their associated models.
    Outputs: None (the text_prompts dictionary is modified in place).
    """
    for name, model in models.items():
        label_names = model.names
        label_list = list(label_names.values())
        cleaned_label_list = clean_labels(label_list)
        for label in cleaned_label_list:
            # Create a unique key for each text-prompt:
            text_to_model_dict[f"{input_text_dict[name]} {label}"] = model
