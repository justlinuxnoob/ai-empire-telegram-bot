# AI Empire · Your own Telegram generator 🤖📸

Text your bot `beach club, white bikini, golden hour` → a photo of **your** AI influencer arrives in the chat.

- **Bot:** a Cloudflare Worker, free forever, never sleeps.
- **Generator:** a RunPod serverless endpoint (Krea 2 Turbo + your LoRA). Costs **$0 while idle**, a few cents per photo.
- **Private:** the bot only answers you.

You need: your LoRA `.safetensors` (from the LoRA Trainer) + its trigger word.

---

## 1 · Put your LoRA online (5 min)
You need a **direct download link** to your LoRA file. Pick one:
- **Google Drive** (easiest): upload → right-click → Share → *General access: Anyone with the link* → Copy link.
- **Dropbox:** upload → Share → Copy link (we fix the `dl=0` part for you).
- **Hugging Face** (if you have an account): upload to a model repo → open the file → copy the **download** link.

## 2 · Make the bot in Telegram (1 min)
Open **@BotFather** → `/newbot` → pick a name → copy the **token** (looks like `123456:ABC...`).

## 3 · Start the generator on RunPod (5 min)
RunPod → **Serverless** → **New Endpoint** → this repo (Hub listing *AI Empire · Telegram Generator*, or *GitHub repo* → `justlinuxnoob/ai-empire-telegram-bot`).
- **GPU:** 24 GB (RTX 4090 / 3090 / L4 / A5000 …)
- **Max workers:** 1 · **Idle timeout:** 5 s · **FlashBoot:** on
- **No settings / env vars needed.**

Copy the **Endpoint ID** (top of the endpoint page). Also make an API key: Settings → API Keys.

## 4 · Start the bot on Cloudflare (5 min, free)
1. dash.cloudflare.com → **Workers & Pages** → **Create** → *Hello World* → name it → **Deploy**.
2. **Edit code** → delete everything → paste [`cloudflare/worker.js`](cloudflare/worker.js) → **Deploy**.
3. **Settings → Variables and Secrets** → add:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | token from BotFather |
| `RUNPOD_API_KEY` | your RunPod API key |
| `RUNPOD_ENDPOINT_ID` | your endpoint ID |
| `LORA_URL` | your LoRA download link |
| `TRIGGER_WORD` | e.g. `zvx woman` |

4. Open `https://<your-worker>.workers.dev/setup` → you should see **✅ Bot connected!**
5. Message your bot → it replies with **your Telegram ID** → add it as `OWNER_ID` → Deploy. Done 🎉

## Using it
Just describe the photo: shot, outfit, place, light. The trigger word is added for you.
Don't describe her face or hair, the LoRA knows her.

⏱ First photo after a break: **1–2 min** (the GPU wakes up and downloads your LoRA). After that: **a few seconds**.

Optional variables: `LORA_STRENGTH` (default `0.9`), `WIDTH` / `HEIGHT` (default `1024` × `1536`).

## Troubleshooting
- **Bot doesn't answer:** open `/setup` again.
- **"RunPod rejected the API key" / "can't find that endpoint":** check those two variables.
- **"the LoRA link didn't give me a .safetensors file":** the link opens a web page, not the file. For Google Drive: sharing must be *Anyone with the link*.
- **Not her face:** check `TRIGGER_WORD` is exactly the one you trained with; try `LORA_STRENGTH` = `1.0`.
