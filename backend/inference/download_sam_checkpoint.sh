#!/bin/bash
# Download SAM model checkpoint

set -e

echo "📥 Downloading Segment Anything Model checkpoint..."
echo ""

# Default to vit_b (lightest/fastest model)
MODEL=${1:-vit_b}

case $MODEL in
  vit_b)
    URL="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
    FILENAME="sam_vit_b_01ec64.pth"
    ;;
  vit_l)
    URL="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth"
    FILENAME="sam_vit_l_0b3195.pth"
    ;;
  vit_h)
    URL="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
    FILENAME="sam_vit_h_4b8939.pth"
    ;;
  *)
    echo "❌ Unknown model: $MODEL"
    echo "Usage: $0 [vit_b|vit_l|vit_h]"
    echo ""
    echo "Models:"
    echo "  vit_b - 91MB  (fastest, recommended for CPU)"
    echo "  vit_l - 358MB (balanced)"
    echo "  vit_h - 2.4GB (best quality, requires GPU)"
    exit 1
    ;;
esac

echo "Model: $MODEL"
echo "URL: $URL"
echo "Output: $FILENAME"
echo ""

# Check if file already exists
if [ -f "$FILENAME" ]; then
  echo "✅ $FILENAME already exists. Skipping download."
  echo "Delete it first if you want to re-download."
  exit 0
fi

# Download using wget or curl
if command -v wget &> /dev/null; then
  wget "$URL" -O "$FILENAME"
elif command -v curl &> /dev/null; then
  curl -L "$URL" -o "$FILENAME"
else
  echo "❌ Neither wget nor curl is available. Please install one of them."
  exit 1
fi

echo ""
echo "✅ Download complete: $FILENAME"
echo ""
echo "To use this model, set environment variable:"
echo "  export SAM_CHECKPOINT=$FILENAME"

