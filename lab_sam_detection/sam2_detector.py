"""
SAM 2 Floating Object Detector

Detector de objetos flutuantes usando SAM 2 (Segment Anything Model 2) da Meta.
"""

import os
import sys
import numpy as np
import cv2
from PIL import Image
import torch


class FloatingObjectDetector:
    """Detector de objetos flutuantes usando segmentação por cor e contornos."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.color_ranges = {
            "rosa": {"lower": [150, 50, 100], "upper": [180, 255, 255], "rgb": (255, 105, 180)},
            "ciano": {"lower": [80, 50, 100], "upper": [100, 255, 255], "rgb": (0, 255, 255)},
            "magenta": {"lower": [130, 50, 100], "upper": [160, 255, 255], "rgb": (255, 0, 255)},
            "azul": {"lower": [100, 50, 100], "upper": [130, 255, 255], "rgb": (0, 100, 255)},
            "roxo": {"lower": [120, 50, 100], "upper": [145, 255, 255], "rgb": (128, 0, 128)},
        }
    
    def detect(self, image_path: str) -> dict:
        """Detecta objetos flutuantes coloridos na imagem."""
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        result = img.copy()
        objects = []
        
        for color_name, color_info in self.color_ranges.items():
            lower = np.array(color_info["lower"])
            upper = np.array(color_info["upper"])
            
            mask = cv2.inRange(hsv, lower, upper)
            
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 800:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    if 0.1 < aspect_ratio < 10.0:
                        bgr_color = color_info["rgb"][::-1]
                        cv2.rectangle(result, (x, y), (x + w, y + h), bgr_color, 3)
                        label = f"{color_name} ({area:.0f}px)"
                        cv2.putText(result, label, (x, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)
                        
                        objects.append({
                            "id": len(objects) + 1,
                            "color": color_name,
                            "bbox": {"x": x, "y": y, "width": w, "height": h},
                            "area": float(area),
                            "aspect_ratio": float(aspect_ratio)
                        })
        
        output_path = os.path.join(self.output_dir, "floating_objects_detected.png")
        cv2.imwrite(output_path, result)
        
        return {
            "total_objects": len(objects),
            "objects": objects,
            "output_image": output_path
        }
    
    def create_segmentation_masks(self, image_path: str) -> str:
        """Cria máscaras de segmentação separadas para cada cor."""
        img = cv2.imread(image_path)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        height, width = img.shape[:2]
        combined_mask = np.zeros((height, width, 3), dtype=np.uint8)
        
        for color_name, color_info in self.color_ranges.items():
            lower = np.array(color_info["lower"])
            upper = np.array(color_info["upper"])
            
            mask = cv2.inRange(hsv, lower, upper)
            
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            color_layer = np.zeros_like(img)
            color_layer[:] = color_info["rgb"][::-1]
            combined_mask[mask > 0] = color_layer[mask > 0]
        
        output_path = os.path.join(self.output_dir, "segmentation_masks.png")
        cv2.imwrite(output_path, combined_mask)
        
        return output_path


class SAM2Detector:
    """Detector usando SAM 2 da Meta."""
    
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.predictor = None
    
    def load_model(self, checkpoint_path: str = None):
        """Carrega o modelo SAM 2."""
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor
            
            if checkpoint_path is None:
                checkpoint_path = f"checkpoints/sam2_hiera_{self.model_size}.pt"
            
            model_cfg = f"sam2_hiera_{self.model_size[0]}.yaml"
            
            self.model = build_sam2(model_cfg, checkpoint_path, device=self.device)
            self.predictor = SAM2ImagePredictor(self.model)
            
            return True
        except ImportError:
            print("[AVISO] SAM 2 não disponível")
            return False
    
    def segment_with_points(self, image_path: str, points: list) -> np.ndarray:
        """Segmenta objetos usando pontos como prompt."""
        if self.predictor is None:
            raise RuntimeError("Modelo não carregado")
        
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image_rgb)
        
        point_coords = np.array(points)
        point_labels = np.ones(len(points))
        
        masks, scores, _ = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=True,
        )
        
        return masks[np.argmax(scores)]


def main():
    print("=" * 60)
    print("  SAM 2 - Segment Anything Model 2")
    print("  Meta AI - Detector de Objetos Flutuantes")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Uso: python sam2_detector.py <caminho_imagem>")
        print()
        print("Sobre o SAM 2:")
        print("  - Modelo de segmentação universal da Meta AI")
        print("  - Lançado em Julho de 2024")
        print("  - Suporta imagens e vídeos")
        print("  - Arquitetura: Hiera Vision Transformer")
        print("  - Modelos: tiny, small, base+, large")
        print()
        print("GitHub: https://github.com/facebookresearch/segment-anything-2")
        return
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"[ERRO] Arquivo não encontrado: {image_path}")
        return
    
    detector = FloatingObjectDetector()
    
    print(f"Processando: {image_path}")
    print()
    
    result = detector.detect(image_path)
    
    print(f"Total de objetos flutuantes detectados: {result['total_objects']}")
    print()
    
    for obj in result["objects"]:
        bbox = obj["bbox"]
        print(f"  #{obj['id']} - {obj['color'].upper()}")
        print(f"      Posição: ({bbox['x']}, {bbox['y']})")
        print(f"      Tamanho: {bbox['width']}x{bbox['height']} px")
        print(f"      Área: {obj['area']:.0f} px²")
        print()
    
    print(f"Imagem com detecções salva em: {result['output_image']}")
    
    mask_path = detector.create_segmentation_masks(image_path)
    print(f"Máscaras de segmentação salvas em: {mask_path}")


if __name__ == "__main__":
    main()
