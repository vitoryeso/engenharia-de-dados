#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obstacle Detector - Extracts obstacle coordinates from generated images.

Uses color segmentation to detect neon-colored obstacles and exports
their coordinates for use in the game engine or 3D model generation.
"""

import os
import json
import numpy as np
import cv2
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class DetectedObstacle:
    """Detected obstacle with coordinates and properties."""
    id: int
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    center: Tuple[int, int]
    area: float
    color_name: str
    color_rgb: Tuple[int, int, int]
    contour: np.ndarray
    mask: np.ndarray


class ObstacleDetector:
    """Detects obstacles in game frames using color segmentation."""
    
    COLOR_RANGES = {
        "hot_pink": {"lower": [150, 100, 100], "upper": [180, 255, 255], "rgb": (255, 0, 128)},
        "cyan": {"lower": [80, 100, 100], "upper": [100, 255, 255], "rgb": (0, 255, 255)},
        "magenta": {"lower": [130, 100, 100], "upper": [160, 255, 255], "rgb": (255, 0, 255)},
        "purple": {"lower": [120, 80, 80], "upper": [145, 255, 255], "rgb": (128, 0, 255)},
        "spring_green": {"lower": [35, 100, 100], "upper": [85, 255, 255], "rgb": (0, 255, 128)},
        "orange": {"lower": [10, 100, 100], "upper": [25, 255, 255], "rgb": (255, 128, 0)},
        "sky_blue": {"lower": [95, 100, 100], "upper": [115, 255, 255], "rgb": (0, 128, 255)},
        "yellow": {"lower": [20, 100, 100], "upper": [35, 255, 255], "rgb": (255, 255, 0)},
    }
    
    def __init__(self, min_area: int = 500):
        self.min_area = min_area
        self.obstacle_id = 0
    
    def detect(self, image: np.ndarray) -> List[DetectedObstacle]:
        """Detect all obstacles in an image."""
        if isinstance(image, str):
            image = cv2.imread(image)
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        detected = []
        
        for color_name, color_info in self.COLOR_RANGES.items():
            lower = np.array(color_info["lower"])
            upper = np.array(color_info["upper"])
            
            mask = cv2.inRange(hsv, lower, upper)
            
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if area >= self.min_area:
                    self.obstacle_id += 1
                    x, y, w, h = cv2.boundingRect(contour)
                    center = (x + w // 2, y + h // 2)
                    
                    obj_mask = np.zeros(image.shape[:2], dtype=np.uint8)
                    cv2.drawContours(obj_mask, [contour], -1, 255, -1)
                    
                    detected.append(DetectedObstacle(
                        id=self.obstacle_id,
                        bbox=(x, y, w, h),
                        center=center,
                        area=area,
                        color_name=color_name,
                        color_rgb=color_info["rgb"],
                        contour=contour,
                        mask=obj_mask
                    ))
        
        return detected
    
    def extract_obstacle_sprites(self, image: np.ndarray, obstacles: List[DetectedObstacle], 
                                  output_dir: str, padding: int = 10) -> List[str]:
        """Extract individual obstacle sprites for 3D conversion."""
        os.makedirs(output_dir, exist_ok=True)
        sprite_paths = []
        
        for obs in obstacles:
            x, y, w, h = obs.bbox
            
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            
            sprite = image[y1:y2, x1:x2].copy()
            
            mask_crop = obs.mask[y1:y2, x1:x2]
            
            sprite_rgba = cv2.cvtColor(sprite, cv2.COLOR_BGR2BGRA)
            sprite_rgba[:, :, 3] = mask_crop
            
            filename = f"obstacle_{obs.id:03d}_{obs.color_name}.png"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, sprite_rgba)
            sprite_paths.append(filepath)
        
        return sprite_paths
    
    def export_coordinates(self, obstacles: List[DetectedObstacle], 
                           image_shape: Tuple[int, int, int]) -> Dict:
        """Export obstacle coordinates for game engine."""
        height, width = image_shape[:2]
        
        data = {
            "image_size": {"width": width, "height": height},
            "obstacles": []
        }
        
        for obs in obstacles:
            x, y, w, h = obs.bbox
            
            norm_x = x / width
            norm_y = y / height
            norm_w = w / width
            norm_h = h / height
            
            data["obstacles"].append({
                "id": obs.id,
                "color": obs.color_name,
                "color_rgb": list(obs.color_rgb),
                "bbox": {"x": x, "y": y, "width": w, "height": h},
                "bbox_normalized": {
                    "x": round(norm_x, 4),
                    "y": round(norm_y, 4),
                    "width": round(norm_w, 4),
                    "height": round(norm_h, 4)
                },
                "center": {"x": obs.center[0], "y": obs.center[1]},
                "area": obs.area,
                "estimated_3d": {
                    "position": {
                        "x": round((norm_x - 0.5) * 10, 2),
                        "y": round((1 - norm_y - norm_h) * 5, 2),
                        "z": round((1 - norm_y) * 20, 2)
                    },
                    "scale": {
                        "x": round(norm_w * 5, 2),
                        "y": round(norm_h * 5, 2),
                        "z": round(min(norm_w, norm_h) * 3, 2)
                    }
                }
            })
        
        return data
    
    def visualize_detections(self, image: np.ndarray, 
                              obstacles: List[DetectedObstacle]) -> np.ndarray:
        """Draw detection results on image."""
        result = image.copy()
        
        for obs in obstacles:
            x, y, w, h = obs.bbox
            color_bgr = obs.color_rgb[::-1]
            
            cv2.rectangle(result, (x, y), (x + w, y + h), color_bgr, 3)
            
            label = f"#{obs.id} {obs.color_name}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(result, (x, y - 20), (x + label_size[0] + 5, y), color_bgr, -1)
            cv2.putText(result, label, (x + 2, y - 6),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            cv2.circle(result, obs.center, 5, (255, 255, 255), -1)
        
        return result


def process_game_frame(image_path: str, output_dir: str) -> Dict:
    """Process a single game frame and extract all obstacle data."""
    os.makedirs(output_dir, exist_ok=True)
    
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    detector = ObstacleDetector()
    obstacles = detector.detect(image)
    
    sprites_dir = os.path.join(output_dir, "sprites")
    sprite_paths = detector.extract_obstacle_sprites(image, obstacles, sprites_dir)
    
    coords = detector.export_coordinates(obstacles, image.shape)
    coords_file = os.path.join(output_dir, "coordinates.json")
    with open(coords_file, 'w') as f:
        json.dump(coords, f, indent=2)
    
    viz = detector.visualize_detections(image, obstacles)
    viz_path = os.path.join(output_dir, "detections.png")
    cv2.imwrite(viz_path, viz)
    
    print(f"Detected {len(obstacles)} obstacles")
    print(f"Sprites saved to: {sprites_dir}")
    print(f"Coordinates saved to: {coords_file}")
    print(f"Visualization saved to: {viz_path}")
    
    return {
        "obstacles": coords,
        "sprites": sprite_paths,
        "visualization": viz_path
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python detector.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_dir = "../output/detected"
    
    result = process_game_frame(image_path, output_dir)
