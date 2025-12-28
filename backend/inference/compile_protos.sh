#!/bin/bash
# Script to compile protobuf definitions to Python

set -e

echo "Compiling protobuf definitions..."

python -m grpc_tools.protoc \
    -I./protos \
    --python_out=. \
    --grpc_python_out=. \
    ./protos/inference.proto

echo "Protobuf compilation complete!"
echo "Generated files:"
echo "  - inference_pb2.py"
echo "  - inference_pb2_grpc.py"

