#!/usr/bin/env python3
"""Cria uma imagem de teste simulando o estilo cyberpunk com objetos flutuantes."""

import numpy as np
import cv2
import os

def create_cyberpunk_test_image():
    """Cria uma imagem de teste com objetos flutuantes neon."""
    width, height = 800, 1000
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            if (x + y) % 40 < 2:
                img[y, x] = [40, 20, 50]
    
    floating_objects = [
        {"pos": (50, 80), "size": (120, 80), "color": (255, 100, 200)},
        {"pos": (250, 50), "size": (100, 60), "color": (255, 255, 100)},
        {"pos": (400, 100), "size": (80, 100), "color": (200, 100, 255)},
        {"pos": (600, 60), "size": (150, 90), "color": (100, 255, 255)},
        {"pos": (30, 300), "size": (70, 70), "color": (255, 50, 150)},
        {"pos": (650, 250), "size": (100, 120), "color": (150, 100, 255)},
        {"pos": (100, 500), "size": (90, 60), "color": (255, 200, 100)},
        {"pos": (600, 500), "size": (80, 80), "color": (100, 255, 200)},
        {"pos": (50, 750), "size": (130, 70), "color": (255, 100, 255)},
        {"pos": (300, 850), "size": (60, 100), "color": (200, 255, 100)},
        {"pos": (550, 800), "size": (110, 80), "color": (100, 200, 255)},
        {"pos": (680, 700), "size": (70, 130), "color": (255, 150, 200)},
    ]
    
    for obj in floating_objects:
        x, y = obj["pos"]
        w, h = obj["size"]
        color = obj["color"]
        cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
        overlay = img.copy()
        cv2.rectangle(overlay, (x - 5, y - 5), (x + w + 5, y + h + 5), color, 2)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    
    center_x, center_y = width // 2, height // 2
    head_center = (center_x, center_y - 150)
    
    for r in range(80, 100, 5):
        cv2.circle(img, head_center, r, (200, 100, 200), 1)
    
    cv2.line(img, (center_x, center_y - 70), (center_x, center_y + 150), (180, 80, 180), 2)
    cv2.line(img, (center_x - 100, center_y), (center_x + 100, center_y), (180, 80, 180), 2)
    cv2.line(img, (center_x, center_y + 150), (center_x - 50, center_y + 280), (180, 80, 180), 2)
    cv2.line(img, (center_x, center_y + 150), (center_x + 50, center_y + 280), (180, 80, 180), 2)
    
    os.makedirs("images", exist_ok=True)
    output_path = "images/cyberpunk_test.png"
    cv2.imwrite(output_path, img)
    print(f"Imagem de teste criada: {output_path}")
    return output_path


if __name__ == "__main__":
    create_cyberpunk_test_image()
