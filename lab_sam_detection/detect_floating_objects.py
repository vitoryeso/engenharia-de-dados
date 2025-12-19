"""
SAM 2 (Segment Anything Model 2) - Detecção de Objetos Flutuantes

O SAM 2 é o modelo de segmentação mais recente da Meta AI, lançado em 2024.
Ele é capaz de segmentar qualquer objeto em imagens e vídeos com alta precisão.

Características principais do SAM 2:
- Segmentação zero-shot (sem necessidade de treino específico)
- Suporte a prompts: pontos, bounding boxes, máscaras
- Arquitetura baseada em Vision Transformer (ViT)
- Memória para tracking em vídeos
- Modelos disponíveis: tiny, small, base+, large
"""

import os
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import torch


def detect_floating_objects_color_based(image_path: str, output_dir: str = "output"):
    """
    Detecta objetos flutuantes na imagem usando segmentação por cor.
    
    Esta abordagem identifica os retângulos coloridos (rosa, ciano, magenta)
    que aparecem flutuando na imagem cyberpunk.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    color_ranges = {
        "rosa": ([150, 50, 50], [180, 255, 255]),
        "ciano": ([80, 50, 50], [100, 255, 255]),
        "magenta": ([130, 50, 50], [160, 255, 255]),
        "azul": ([100, 50, 50], [130, 255, 255]),
    }
    
    result = img.copy()
    detected_objects = []
    
    for color_name, (lower, upper) in color_ranges.items():
        lower = np.array(lower)
        upper = np.array(upper)
        
        mask = cv2.inRange(hsv, lower, upper)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                if 0.2 < aspect_ratio < 5.0:
                    cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(result, f"{color_name}", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    detected_objects.append({
                        "color": color_name,
                        "bbox": (x, y, w, h),
                        "area": area
                    })
    
    output_path = os.path.join(output_dir, "detected_floating_objects.png")
    cv2.imwrite(output_path, result)
    
    print(f"Objetos flutuantes detectados: {len(detected_objects)}")
    for i, obj in enumerate(detected_objects):
        print(f"  {i+1}. Cor: {obj['color']}, Área: {obj['area']:.0f}px², BBox: {obj['bbox']}")
    
    return detected_objects, output_path


def detect_with_sam2_automatic(image_path: str, output_dir: str = "output"):
    """
    Usa SAM 2 para segmentação automática de todos os objetos na imagem.
    
    O SAM 2 possui um gerador automático de máscaras que identifica
    todos os objetos potenciais na imagem.
    """
    try:
        from sam2.build_sam import build_sam2
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    except ImportError:
        print("[AVISO] SAM 2 não instalado. Instale com: pip install segment-anything-2")
        print("Usando método alternativo baseado em cor...")
        return detect_floating_objects_color_based(image_path, output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Usando dispositivo: {device}")
    
    checkpoint = "sam2_hiera_large.pt"
    model_cfg = "sam2_hiera_l.yaml"
    
    if not os.path.exists(checkpoint):
        print(f"[AVISO] Checkpoint não encontrado: {checkpoint}")
        print("Baixe de: https://github.com/facebookresearch/segment-anything-2")
        return detect_floating_objects_color_based(image_path, output_dir)
    
    sam2 = build_sam2(model_cfg, checkpoint, device=device)
    mask_generator = SAM2AutomaticMaskGenerator(
        model=sam2,
        points_per_side=32,
        pred_iou_thresh=0.86,
        stability_score_thresh=0.92,
        min_mask_region_area=100,
    )
    
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    print("Gerando máscaras automaticamente...")
    masks = mask_generator.generate(image_rgb)
    
    print(f"Total de objetos segmentados: {len(masks)}")
    
    result = image.copy()
    for i, mask_data in enumerate(masks):
        mask = mask_data["segmentation"]
        color = np.random.randint(0, 255, 3).tolist()
        result[mask] = result[mask] * 0.5 + np.array(color) * 0.5
    
    output_path = os.path.join(output_dir, "sam2_segmentation.png")
    cv2.imwrite(output_path, result)
    
    return masks, output_path


def detect_with_point_prompts(image_path: str, points: list, output_dir: str = "output"):
    """
    Usa SAM 2 com prompts de pontos para segmentar objetos específicos.
    
    Args:
        image_path: Caminho para a imagem
        points: Lista de coordenadas (x, y) para os objetos a segmentar
        output_dir: Diretório de saída
    """
    try:
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor
    except ImportError:
        print("[AVISO] SAM 2 não instalado.")
        return None
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    checkpoint = "sam2_hiera_large.pt"
    model_cfg = "sam2_hiera_l.yaml"
    
    sam2 = build_sam2(model_cfg, checkpoint, device=device)
    predictor = SAM2ImagePredictor(sam2)
    
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    predictor.set_image(image_rgb)
    
    point_coords = np.array(points)
    point_labels = np.ones(len(points))
    
    masks, scores, _ = predictor.predict(
        point_coords=point_coords,
        point_labels=point_labels,
        multimask_output=True,
    )
    
    return masks, scores


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "images/cyberpunk_image.png"
    
    print("=" * 60)
    print("SAM 2 - Segment Anything Model 2 (Meta AI)")
    print("=" * 60)
    print()
    print("Sobre o SAM 2:")
    print("- Modelo de segmentação state-of-the-art da Meta")
    print("- Lançado em julho de 2024")
    print("- Suporta imagens e vídeos")
    print("- Zero-shot: funciona sem treino adicional")
    print()
    
    if os.path.exists(image_path):
        objects, output_path = detect_floating_objects_color_based(image_path, "output")
        print(f"\nResultado salvo em: {output_path}")
    else:
        print(f"[ERRO] Imagem não encontrada: {image_path}")
        print("Coloque a imagem no diretório 'images/' e execute novamente.")
