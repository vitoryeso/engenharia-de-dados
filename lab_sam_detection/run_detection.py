#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de Objetos Flutuantes usando técnicas de segmentação.

Para a imagem cyberpunk fornecida, detecta os retângulos coloridos flutuantes
(rosa, ciano, magenta, azul, roxo) ao redor da figura wireframe.

Uso: python run_detection.py <caminho_imagem>
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path


def detect_floating_objects(image_path: str):
    """
    Detecta objetos flutuantes coloridos na imagem.
    
    Na imagem cyberpunk, os objetos flutuantes são retângulos/quadrados
    em cores neon (rosa, ciano, magenta, azul, roxo) que aparecem
    ao redor da figura central do humanóide wireframe.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"[ERRO] Não foi possível carregar: {image_path}")
        return None
    
    print(f"Imagem carregada: {img.shape[1]}x{img.shape[0]} px")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    result = img.copy()
    
    neon_colors = {
        "rosa": {
            "hsv_lower": [150, 80, 150],
            "hsv_upper": [180, 255, 255],
            "draw_color": (180, 105, 255)
        },
        "ciano": {
            "hsv_lower": [80, 80, 150],
            "hsv_upper": [100, 255, 255],
            "draw_color": (255, 255, 0)
        },
        "magenta": {
            "hsv_lower": [130, 80, 150],
            "hsv_upper": [155, 255, 255],
            "draw_color": (255, 0, 255)
        },
        "azul": {
            "hsv_lower": [100, 80, 150],
            "hsv_upper": [130, 255, 255],
            "draw_color": (255, 128, 0)
        },
        "roxo": {
            "hsv_lower": [120, 50, 100],
            "hsv_upper": [145, 255, 255],
            "draw_color": (255, 0, 128)
        },
    }
    
    all_objects = []
    
    for color_name, color_cfg in neon_colors.items():
        lower = np.array(color_cfg["hsv_lower"])
        upper = np.array(color_cfg["hsv_upper"])
        draw_color = color_cfg["draw_color"]
        
        mask = cv2.inRange(hsv, lower, upper)
        
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                
                rect_area = w * h
                fill_ratio = area / rect_area if rect_area > 0 else 0
                
                if fill_ratio > 0.3:
                    cv2.rectangle(result, (x, y), (x + w, y + h), draw_color, 3)
                    
                    label = f"{color_name}"
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(result, (x, y - 25), (x + label_size[0] + 5, y), draw_color, -1)
                    cv2.putText(result, label, (x + 2, y - 8),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                    
                    all_objects.append({
                        "color": color_name,
                        "position": (x, y),
                        "size": (w, h),
                        "area": area,
                        "fill_ratio": fill_ratio
                    })
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "detected_floating_objects.png"
    cv2.imwrite(str(output_path), result)
    
    return all_objects, str(output_path)


def main():
    print("=" * 65)
    print("  DETECTOR DE OBJETOS FLUTUANTES")
    print("  Baseado em técnicas de segmentação (SAM 2 style)")
    print("=" * 65)
    print()
    
    if len(sys.argv) < 2:
        print("Uso: python run_detection.py <imagem>")
        print()
        print("Sobre o SAM 2 (Segment Anything Model 2):")
        print("  - Modelo de segmentação universal da Meta AI (Jul/2024)")
        print("  - Segmenta qualquer objeto em imagens e vídeos")
        print("  - Suporta prompts: pontos, bounding boxes, máscaras")
        print("  - Arquitetura: Hiera Vision Transformer")
        print()
        print("Este script usa uma abordagem baseada em cor para detectar")
        print("objetos flutuantes neon típicos de imagens cyberpunk.")
        return
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"[ERRO] Arquivo não encontrado: {image_path}")
        return
    
    print(f"Processando: {image_path}")
    print()
    
    result = detect_floating_objects(image_path)
    
    if result is None:
        return
    
    objects, output_path = result
    
    print(f"\nObjetos flutuantes detectados: {len(objects)}")
    print("-" * 45)
    
    color_counts = {}
    for obj in objects:
        color = obj["color"]
        color_counts[color] = color_counts.get(color, 0) + 1
    
    for color, count in sorted(color_counts.items()):
        print(f"  {color.upper():12} : {count} objetos")
    
    print("-" * 45)
    print(f"\nResultado salvo em: {output_path}")


if __name__ == "__main__":
    main()
