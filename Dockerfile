# syntax=docker/dockerfile:1
# AI Empire · Telegram generator (RunPod serverless worker)
# Krea 2 Turbo + YOUR character LoRA -> the photo is sent straight to your Telegram chat.
# The LoRA link, trigger word and Telegram token come with each job (set once in the Cloudflare bot),
# so this endpoint needs no settings at all.
FROM runpod/worker-comfyui:5.10.0-base

# ---------------------------------------------------------------------------
# Models first (~18 GB, never change): Krea 2 Turbo fp8 + Qwen3-VL 4B fp8 + Qwen-Image VAE.
# Open Comfy-Org repack: no Hugging Face login needed.
# ---------------------------------------------------------------------------
RUN comfy model download \
    --url https://huggingface.co/Comfy-Org/Krea-2/resolve/main/diffusion_models/krea2_turbo_fp8_scaled.safetensors \
    --relative-path models/diffusion_models --filename krea2_turbo_fp8_scaled.safetensors
RUN comfy model download \
    --url https://huggingface.co/Comfy-Org/Krea-2/resolve/main/text_encoders/qwen3vl_4b_fp8_scaled.safetensors \
    --relative-path models/text_encoders --filename qwen3vl_4b_fp8_scaled.safetensors
RUN comfy model download \
    --url https://huggingface.co/Comfy-Org/Krea-2/resolve/main/vae/qwen_image_vae.safetensors \
    --relative-path models/vae --filename qwen_image_vae.safetensors

# ---------------------------------------------------------------------------
# Newer ComfyUI: the 5.10.0 base ships ComfyUI 0.34.0; Krea 2 repacks want a current one.
# Same pins as the base image keep huggingface-hub < 1.0 (hub 1.x breaks ComfyUI start-up).
# ---------------------------------------------------------------------------
ARG COMFY_TAG=v0.38.2
RUN git clone --depth 1 --branch ${COMFY_TAG} https://github.com/comfyanonymous/ComfyUI.git /tmp/comfy-new \
    && rm -rf /tmp/comfy-new/models /tmp/comfy-new/custom_nodes \
    && cp -a /tmp/comfy-new/. /comfyui/ && rm -rf /tmp/comfy-new \
    && uv pip install -r /comfyui/requirements.txt \
    && uv pip install "transformers>=4.50.3,<5" "huggingface-hub<1.0" gdown

# boot ComfyUI once on CPU: a broken install fails the BUILD, not your first Telegram message
RUN cd /comfyui && timeout 300 python main.py --quick-test-for-ci --cpu

# our handler replaces the stock one (the base start.sh runs /handler.py)
COPY handler.py /handler.py
