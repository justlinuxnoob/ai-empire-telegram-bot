# AI Empire · Your own Telegram generator

**▶ New here? Start with the free video series: [joinaiempire.com/video](https://joinaiempire.com/video)** (video 1: make your first AI face).
Guides and the full course: https://joinaiempire.com

Text your bot a prompt. A photo of **your** AI character arrives in the chat.

- **Bot:** a Cloudflare Worker on the free plan. It never sleeps.
- **Generator:** a RunPod Serverless endpoint running Krea 2 Turbo with your LoRA. It costs **$0 while idle**. You pay only while the GPU makes a photo.
- **Private:** the bot answers only you.

You need:

- your character LoRA (a `.safetensors` file trained on Krea 2, since that is the model this generator runs)
- its trigger word
- a Telegram account, a RunPod account and a free Cloudflare account

Use it for an original AI character only. Never a real person's face.

---

## 1 · Put your LoRA online

The generator downloads your LoRA from a link. Pick one:

- **Google Drive:** upload the file → right-click → Share → General access: **Anyone with the link** → Copy link. The generator turns it into a direct download for you, big files included.
- **Dropbox:** upload → Share → Copy link. The generator changes `dl=0` to `dl=1` for you.
- **Hugging Face** (if you have an account): upload to a model repo and copy the file's link. A `/blob/` link is changed to `/resolve/` for you.

## 2 · Make the bot in Telegram

Open **@BotFather** → `/newbot` → pick a name and a username → copy the **token** (it looks like `123456:ABC...`).

## 3 · Start the generator on RunPod

RunPod → **Serverless** → **New Endpoint** → deploy from GitHub: `justlinuxnoob/ai-empire-telegram-bot`. RunPod builds the image from the `Dockerfile` in this repo. The first build takes a while (the models are about 18 GB).

Settings:

- **GPU:** 24 GB
- **Max workers:** 1
- **Idle timeout:** 5 s
- **FlashBoot:** on
- **Container disk:** 30 GB
- **Environment variables:** none. The bot sends everything with each job.

When it's ready, copy the **Endpoint ID** from the top of the endpoint page.
Then make an API key: RunPod → **Settings** → **API Keys**.

## 4 · Start the bot on Cloudflare (free)

1. dash.cloudflare.com → **Workers & Pages** → **Create** → *Hello World* → name it → **Deploy**.
2. **Edit code** → delete everything → paste [`cloudflare/worker.js`](cloudflare/worker.js) → **Deploy**.
3. **Settings → Variables and Secrets** → add these:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the token from BotFather |
| `RUNPOD_API_KEY` | your RunPod API key |
| `RUNPOD_ENDPOINT_ID` | your endpoint ID |
| `LORA_URL` | your LoRA link from step 1 |
| `OWNER_ID` | leave it for now, you get it in step 5 |

4. Deploy, then open `https://<your-worker>.workers.dev/setup`. You should see **"Bot connected!"**
5. Open your bot in Telegram and send it any message. It replies with **your Telegram ID**.
6. Add that number as `OWNER_ID` → **Deploy**. Message the bot again. Done.

`OWNER_ID` makes the bot answer only you, so nobody else can spend your RunPod credits. To let a second account use it, put both IDs in, separated by a comma.

### Optional variables

| Name | Default | What it does |
|---|---|---|
| `LORA_STRENGTH` | `0.9` | How strongly the LoRA is applied |
| `WIDTH` | `1024` | Image width in pixels |
| `HEIGHT` | `1536` | Image height in pixels (portrait) |

## How to write a prompt

Same rule as the course:

1. Type the **trigger word**.
2. One short **hair and eyes** line.
3. The **scene**: photo type, pose, outfit, place, light, framing.
4. End with `candid smartphone photo, natural skin texture`.

Example:

```
zvx woman, long wavy dark brown hair, middle part, hazel eyes, sitting at a cafe table by the window, cream knit sweater, soft morning light, medium shot, candid smartphone photo, natural skin texture
```

Don't describe her face shape, makeup, skin or body. The LoRA knows her face.

If you forget the ending, the generator adds `candid smartphone photo, natural skin texture` for you. It does **not** add the trigger word: type it yourself every time.

The photo comes back with your full prompt as its caption, so you can copy what worked.

Send `/start` or `/help` to see a short help message.

### How long it takes

- First photo after a break: **1 to 2 minutes**. The GPU wakes up and downloads your LoRA.
- After that: **a few seconds** each.

The bot replies "On it…" as soon as RunPod takes the job.

## Troubleshooting

- **Bot doesn't answer:** open `/setup` again. If it says "Missing variables", add the ones it lists and deploy. If it says "Telegram said: …", check `TELEGRAM_BOT_TOKEN`.
- **"This is a private bot.":** the account you're messaging from isn't in `OWNER_ID`.
- **"RunPod rejected the API key (check RUNPOD_API_KEY)":** make a new API key and paste it again.
- **"RunPod can't find that endpoint (check RUNPOD_ENDPOINT_ID)":** copy the endpoint ID again from the endpoint page.
- **"Something went wrong: the LoRA link didn't give me a .safetensors file.":** the link opens a web page, not the file. For Google Drive, sharing must be **Anyone with the link**. For Hugging Face, the repo must be public.
- **Not her face:** start the prompt with exactly the trigger word you trained with. Still off? Set `LORA_STRENGTH` to `1.0`.
- **Changed your LoRA:** update `LORA_URL` and deploy. The new file downloads on the next photo, so that one is slow again.
