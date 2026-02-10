# RunPod Deployment Plan (HeartMuLa / heartlib)

This document summarizes **all issues encountered** and provides a **clean, fast, reproducible deployment plan** for running HeartMuLa **from the console** on RunPod.
UI (Gradio / ComfyUI) is intentionally excluded from the critical path.

---

## 1. Problems Encountered & Resolutions

### A. Local GPU unusable (Windows)
- **Symptom:** `CUDA available: False`, GPU Code 43
- **Cause:** Broken / unsupported NVIDIA GPU & drivers
- **Resolution:** Stop local attempts → use cloud GPU (RunPod)

---

### B. Model downloads incomplete (symlinks, tiny folders)
- **Symptom:** Model folders only a few MB, missing `.safetensors`
- **Cause:** `hf download` creates symlinks or incomplete pulls in containers
- **Resolution:** Use `huggingface_hub.snapshot_download()` or verified full downloads

---

### C. “Disk quota exceeded” despite large storage
- **Symptom:** `OSError: [Errno 122] Disk quota exceeded`
- **Cause:** HuggingFace cache defaulting to `/root/.cache` (small overlay FS)
- **Resolution:** Force cache and temp dirs to `/workspace`:
  ```bash
  export HF_HOME=/workspace/.cache/huggingface
  export TMPDIR=/workspace/tmp
  ```

---

### D. Incorrect model directory structure
- **Symptom:** `Expected to find checkpoint ... HeartMuLa-oss-3B`
- **Cause:** Model files not placed in expected subfolders
- **Resolution:** Respect exact directory layout required by heartlib

---

### E. Conda not available
- **Symptom:** `conda: command not found`
- **Resolution:** Use Python `venv` instead of conda

---

### F. Audio playback fails with ffplay
- **Symptom:** ALSA / audio device errors
- **Cause:** Containers have no audio devices
- **Resolution:** Serve audio via HTTP and listen in browser

---

### G. UI (Gradio) API mismatches
- **Symptom:** `unexpected keyword argument`, indentation errors
- **Cause:** UI code not aligned with pipeline API
- **Decision:** Postpone UI until console workflow is stable

---

### H. RunPod ports not accessible
- **Symptom:** “Port not ready”
- **Cause:** Port not exposed in Pod config
- **Resolution:** Explicitly expose required HTTP ports

---

## 2. Target Environment (Minimal)

- **GPU:** NVIDIA A40 (or equivalent)
- **Storage:** ≥ 60 GB (recommended 80–100 GB)
- **OS:** Linux (RunPod default)
- **Ports:** None required for console (optional: 7862 for audio playback)

---

## 3. Fast Deployment Plan (Console Only)

### Step 0 — Prepare directories & environment variables
```bash
export HF_HOME=/workspace/.cache/huggingface
export TMPDIR=/workspace/tmp
mkdir -p /workspace/.cache/huggingface /workspace/tmp /workspace/ckpt
```

---

### Step 1 — Clone repository
```bash
cd /workspace
git clone https://github.com/joanjus/heartlib.git
cd heartlib
```

---

### Step 2 — Create and activate virtual environment
```bash
python3 -m venv /workspace/venvs/heartmula
source /workspace/venvs/heartmula/bin/activate
python -m pip install --upgrade pip
```

---

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

Verify CUDA:
```bash
python - <<'PY'
import torch
print("CUDA available:", torch.cuda.is_available())
print("Torch:", torch.__version__)
PY
```

---

### Step 4 — Download models correctly
- Use **full downloads** (no symlinks)
- Place files in `/workspace/ckpt`
- Verify:
```bash
du -sh /workspace/ckpt
find /workspace/ckpt -name "*.safetensors" | head
```

Files should be **GB-sized**, not MB.

---

### Step 5 — Run console example
```bash
cd /workspace/heartlib
python examples/run_music_generation.py --model_path=/workspace/ckpt --version=3B
```

Expected:
- Model shards load
- Generation progress
- MP3 output created

---

## 4. Listening to Output (Recommended)

Serve generated audio via HTTP:

```bash
cd /workspace/heartlib/assets
python -m http.server 7862 --bind 0.0.0.0
```

Expose port **7862** in RunPod → open link → click MP3.

---

## 5. One-Command Restart Script

Create `start_console.sh`:

```bash
cat > start_console.sh <<'SH'
#!/usr/bin/env bash
set -e

export HF_HOME=/workspace/.cache/huggingface
export TMPDIR=/workspace/tmp
mkdir -p "$HF_HOME" "$TMPDIR"

source /workspace/venvs/heartmula/bin/activate
cd /workspace/heartlib

python examples/run_music_generation.py --model_path=/workspace/ckpt --version=3B
SH

chmod +x start_console.sh
```

Usage:
```bash
./start_console.sh
```

---

## 6. Priority Order (Do Not Skip)

1. Console generation works reliably
2. Model downloads are documented & repeatable
3. One-command startup
4. UI integration (optional, later)

---

**Status:** Console pipeline validated.  
**Next steps:** Refine prompts, durations, styles — then revisit UI safely.
