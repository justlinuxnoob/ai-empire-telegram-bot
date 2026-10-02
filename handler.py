"""AI Empire · Telegram generator: RunPod serverless handler.

Job input (sent by the Cloudflare bot):
  prompt          what to make, e.g. "beach club, white bikini, golden hour"
  trigger         LoRA trigger word, added in front of the prompt if missing (e.g. "zvx woman")
  lora_url        direct link to your LoRA .safetensors (Hugging Face, Dropbox or Google Drive)
  lora_strength   default 0.9
  telegram_token  your bot token  } when given, the photo is sent straight to this chat
  chat_id         your chat id    }
  width, height   default 1024 x 1536 (portrait)
Without telegram_token the image comes back as base64 (used by the RunPod Hub test).
"""
import base64
import hashlib
import io
import os
import random
import re
import time
import uuid

import requests
import runpod

COMFY = "http://127.0.0.1:8188"
LORA_DIR = "/comfyui/models/loras"
SUFFIX = "candid smartphone photo, natural skin texture"


def log(*a):
    print("[ai-empire]", *a, flush=True)


# ------------------------------------------------------------------ ComfyUI
def wait_for_comfy(timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if requests.get(COMFY + "/system_stats", timeout=5).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("ComfyUI did not start")


def workflow(prompt, lora, strength, width, height, seed):
    model = ["2", 0]
    wf = {
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["3", 0]}},
        "7": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "8": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["4", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"filename_prefix": "tg", "images": ["10", 0]}},
    }
    if lora:
        wf["5"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": lora, "strength_model": strength, "model": ["2", 0]}}
        model = ["5", 0]
    wf["9"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        "model": model, "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["8", 0]}}
    return wf


def generate(wf, timeout=600):
    r = requests.post(COMFY + "/prompt", json={"prompt": wf, "client_id": str(uuid.uuid4())}, timeout=30)
    if not r.ok:
        raise RuntimeError(f"ComfyUI refused the job: {r.text[:500]}")
    pid = r.json()["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = requests.get(f"{COMFY}/history/{pid}", timeout=30).json().get(pid)
        if h:
            status = h.get("status", {})
            if status.get("status_str") == "error":
                msgs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                raise RuntimeError(f"generation failed: {msgs[-1][1].get('exception_message', '')[:300] if msgs else 'unknown error'}")
            for out in h.get("outputs", {}).values():
                for img in out.get("images", []):
                    v = requests.get(f"{COMFY}/view", params={"filename": img["filename"], "subfolder": img.get("subfolder", ""),
                                                             "type": img.get("type", "output")}, timeout=60)
                    v.raise_for_status()
                    return v.content
        time.sleep(0.5)
    raise RuntimeError("generation timed out")


# ------------------------------------------------------------------ LoRA download (cached per worker)
def drive_id(url):
    """File id from any Google Drive share link."""
    m = re.search(r"/file/d/([A-Za-z0-9_-]{10,})", url) or re.search(r"[?&]id=([A-Za-z0-9_-]{10,})", url)
    return m.group(1) if m else None


def direct_link(url):
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        fid = drive_id(url)
        if fid:  # confirm=t skips Google's "can't scan this big file for viruses" page
            return f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    if "dropbox.com" in url:
        url = url.replace("dl=0", "dl=1")
        if "dl=1" not in url:
            url += ("&" if "?" in url else "?") + "dl=1"
    if "huggingface.co" in url and "/blob/" in url:
        url = url.replace("/blob/", "/resolve/")
    return url


def fetch_lora(url):
    os.makedirs(LORA_DIR, exist_ok=True)
    name = "char_" + hashlib.sha1(url.encode()).hexdigest()[:12] + ".safetensors"
    path = os.path.join(LORA_DIR, name)
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        return name
    tmp = path + ".part"
    log("downloading LoRA")
    with requests.get(direct_link(url), stream=True, timeout=60, allow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(8 << 20):
                f.write(chunk)
    ok = False
    if os.path.exists(tmp) and os.path.getsize(tmp) > 1_000_000:
        with open(tmp, "rb") as f:
            head = f.read(9)
        ok = len(head) == 9 and head[8:9] == b"{"  # safetensors: 8-byte length + JSON header
    if not ok:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError("the LoRA link didn't give me a .safetensors file. Use a direct download link "
                           "(Hugging Face, Dropbox, or a Google Drive file shared with 'Anyone with the link').")
    os.replace(tmp, path)
    log("LoRA ready", round(os.path.getsize(path) / 1e6), "MB")
    return name


# ------------------------------------------------------------------ Telegram
def tg(token, method, data=None, files=None):
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=data, files=files, timeout=120)
    return r.ok and r.json().get("ok", False)


def to_jpeg(png_bytes, quality=95):
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO()
    im.save(out, "JPEG", quality=quality)
    return out.getvalue()


# ------------------------------------------------------------------ handler
def handler(job):
    inp = job.get("input") or {}
    token, chat = (inp.get("telegram_token") or "").strip(), inp.get("chat_id")
    try:
        prompt = (inp.get("prompt") or "").strip()
        if not prompt:
            raise RuntimeError("empty prompt")
        trigger = (inp.get("trigger") or "").strip()
        if trigger and not prompt.lower().startswith(trigger.lower()):
            prompt = f"{trigger}, {prompt}"
        if SUFFIX not in prompt:
            prompt = f"{prompt.rstrip(' ,.')}, {SUFFIX}"
        if token and chat:
            tg(token, "sendChatAction", {"chat_id": chat, "action": "upload_photo"})
        lora = fetch_lora(inp["lora_url"].strip()) if (inp.get("lora_url") or "").strip() else None
        width = int(inp.get("width") or 1024)
        height = int(inp.get("height") or 1536)
        strength = float(inp.get("lora_strength") or 0.9)
        seed = random.randint(1, 2**48)
        wait_for_comfy()
        t0 = time.time()
        jpg = to_jpeg(generate(workflow(prompt, lora, strength, width, height, seed)))
        log(f"image ready in {time.time() - t0:.1f}s")
        if token and chat:
            caption = prompt[:1000]
            files = {"photo": ("photo.jpg", jpg, "image/jpeg")}
            if not tg(token, "sendPhoto", {"chat_id": chat, "caption": caption}, files):
                tg(token, "sendDocument", {"chat_id": chat, "caption": caption}, {"document": ("photo.jpg", jpg, "image/jpeg")})
            return {"ok": True, "seed": seed}
        return {"ok": True, "seed": seed, "image": base64.b64encode(jpg).decode()}
    except Exception as e:
        log("error:", e)
        if token and chat:
            tg(token, "sendMessage", {"chat_id": chat, "text": f"⚠️ Something went wrong: {e}"})
        return {"error": str(e)}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
