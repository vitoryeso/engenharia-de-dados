#!/bin/bash

echo "=========================================="
echo "Setup SAM 2 - Segment Anything Model 2"
echo "=========================================="

pip install torch torchvision --quiet
pip install opencv-python numpy matplotlib Pillow --quiet

echo "Instalando SAM 2..."
pip install git+https://github.com/facebookresearch/segment-anything-2.git --quiet

echo "Baixando modelo SAM 2..."
mkdir -p checkpoints
cd checkpoints

if [ ! -f "sam2_hiera_small.pt" ]; then
    wget -q https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_small.pt
fi

cd ..

echo "Setup completo!"
echo "Execute: python detect_floating_objects.py <caminho_imagem>"
