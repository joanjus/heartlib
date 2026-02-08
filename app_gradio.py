# app_gradio.py
# HeartMuLa minimal UI (Gradio) + Dark Mode serio + manejo de errores legible

import os
import time
import tempfile
import gradio as gr

_PIPE = None
_PIPE_CFG = None


def _cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def get_pipe(model_path, version, mula_device, codec_device, mula_dtype, codec_dtype, lazy_load):
    global _PIPE, _PIPE_CFG

    cfg = (
        os.path.abspath(model_path),
        str(version),
        str(mula_device),
        str(codec_device),
        str(mula_dtype),
        str(codec_dtype),
        bool(lazy_load),
    )

    if _PIPE is None or _PIPE_CFG != cfg:
        from heartlib import HeartMuLaGenPipeline  # lazy import

        _PIPE = HeartMuLaGenPipeline(
            model_path=model_path,
            version=version,
            mula_device=mula_device,
            codec_device=codec_device,
            mula_dtype=mula_dtype,
            codec_dtype=codec_dtype,
            lazy_load=bool(lazy_load),
        )
        _PIPE_CFG = cfg

    return _PIPE


def generate(
    model_path,
    version,
    lyrics,
    tags,
    save_name,
    max_audio_length_ms,
    topk,
    temperature,
    cfg_scale,
    mula_device,
    codec_device,
    mula_dtype,
    codec_dtype,
    lazy_load,
):
    wants_cuda = str(mula_device).startswith("cuda") or str(codec_device).startswith("cuda")
    if wants_cuda and not _cuda_available():
        return (
            None,
            "Este equipo no tiene CUDA disponible (o el driver/GPU no está operativo).\n"
            "La UI funciona, pero la generación requiere una GPU NVIDIA con CUDA funcionando.\n\n"
            "Sugerencia: ejecútalo en cloud (Linux+CUDA) o en un PC con NVIDIA moderna.",
        )

    t0 = time.time()

    try:
        with tempfile.TemporaryDirectory() as td:
            lyrics_path = os.path.join(td, "lyrics.txt")
            tags_path = os.path.join(td, "tags.txt")

            save_name = (save_name or "output_ui.mp3").strip()
            if not save_name.lower().endswith(".mp3"):
                save_name += ".mp3"

            out_path_tmp = os.path.join(td, save_name)

            with open(lyrics_path, "w", encoding="utf-8") as f:
                f.write((lyrics or "").rstrip() + "\n")
            with open(tags_path, "w", encoding="utf-8") as f:
                f.write((tags or "").rstrip() + "\n")

            pipe = get_pipe(model_path, version, mula_device, codec_device, mula_dtype, codec_dtype, lazy_load)

            pipe(
                lyrics=lyrics_path,
                tags=tags_path,
                save_path=out_path_tmp,
                max_audio_length_ms=int(max_audio_length_ms),
                topk=int(topk),
                temperature=float(temperature),
                cfg_scale=float(cfg_scale),
            )

            final_dir = os.path.join(os.getcwd(), "ui_outputs")
            os.makedirs(final_dir, exist_ok=True)
            final_path = os.path.join(final_dir, os.path.basename(out_path_tmp))

            with open(out_path_tmp, "rb") as src, open(final_path, "wb") as dst:
                dst.write(src.read())

        dt = time.time() - t0
        log = (
            "OK ✅\n"
            f"- output: {final_path}\n"
            f"- time: {dt:.2f} s\n"
            f"- model_path: {model_path}\n"
            f"- version: {version}\n"
            f"- devices: mula={mula_device}, codec={codec_device}\n"
            f"- dtypes: mula={mula_dtype}, codec={codec_dtype}\n"
            f"- max_audio_length_ms: {max_audio_length_ms}\n"
            f"- topk: {topk}, temperature: {temperature}, cfg_scale: {cfg_scale}\n"
            f"- lazy_load: {lazy_load}\n\n"
            "Tip: si te da OOM, baja duración y/o sube lazy_load."
        )
        return final_path, log

    except Exception as e:
        dt = time.time() - t0
        err = (
            "Error ❌\n"
            f"- time: {dt:.2f} s\n"
            f"- message: {type(e).__name__}: {e}\n\n"
            "Si esto es un error de CUDA/VRAM:\n"
            "- Prueba max_audio_length_ms más bajo (p.ej. 10000)\n"
            "- Prueba lazy_load=True\n"
            "- En cloud usa una GPU con >= 12GB (mejor 24GB para 3B)\n"
        )
        return None, err


DARK_CSS = """
/* --- Base --- */
:root { color-scheme: dark; }
body, .gradio-container {
  background: #0b0f14 !important;
  color: #e6edf3 !important;
}

/* --- Cards / panels --- */
.gradio-container .prose,
.gradio-container .wrap,
.gradio-container .block,
.gradio-container .panel,
.gradio-container .form,
.gradio-container .container {
  color: #e6edf3 !important;
}

/* Many Gradio layouts are in "blocks" */
.gradio-container .gr-block,
.gradio-container .gr-box,
.gradio-container .gr-panel,
.gradio-container .gr-form,
.gradio-container .gr-group {
  background: #0f1620 !important;
  border: 1px solid #1e2a36 !important;
  border-radius: 12px !important;
}

/* --- Labels & help text --- */
label, .label, .gr-label, .info, .hint, .svelte-1ipelgc, .svelte-1gfkn6j {
  color: #c7d1db !important;
}

/* --- Inputs / Textareas / Selects --- */
input, textarea, select {
  background: #0b1320 !important;
  color: #e6edf3 !important;
  border: 1px solid #2b3a4a !important;
  border-radius: 10px !important;
}

input::placeholder, textarea::placeholder {
  color: #7f8b97 !important;
}

/* Some Gradio inputs wrap native inputs */
.gradio-container .wrap input,
.gradio-container .wrap textarea,
.gradio-container .wrap select {
  background: #0b1320 !important;
  color: #e6edf3 !important;
  border: 1px solid #2b3a4a !important;
}

/* Focus */
input:focus, textarea:focus, select:focus {
  outline: none !important;
  border-color: #5aa9ff !important;
  box-shadow: 0 0 0 3px rgba(90,169,255,0.15) !important;
}

/* --- Buttons --- */
button, .gr-button {
  border-radius: 12px !important;
  border: 1px solid #2b3a4a !important;
}
button.primary, .gr-button-primary {
  background: #1f6feb !important;
  border-color: #1f6feb !important;
  color: #ffffff !important;
}
button:hover, .gr-button:hover {
  filter: brightness(1.05) !important;
}

/* --- Slider / progress bits (best-effort) --- */
input[type="range"] {
  accent-color: #5aa9ff !important;
}

/* --- Checkbox / toggle (best-effort) --- */
input[type="checkbox"] {
  accent-color: #5aa9ff !important;
}

/* --- Audio player panel --- */
audio {
  width: 100% !important;
  filter: invert(1) hue-rotate(180deg) saturate(1.2);
}

/* --- Reduce spacing a bit --- */
.gradio-container .gr-block, .gradio-container .gr-box {
  padding: 12px !important;
}
"""


demo = gr.Blocks(
    title="HeartMuLa – UI mínima",
    theme=gr.themes.Soft(),
    css=DARK_CSS,
)

with demo:
    gr.Markdown(
        "## HeartMuLa – interfaz mínima (dark mode)\n"
        "Genera un MP3 usando el pipeline oficial (sin tocar la CLI)."
    )

    with gr.Row():
        model_path = gr.Textbox(value="./ckpt", label="Model path (ckpt)")
        version = gr.Dropdown(choices=["3B"], value="3B", label="Version")

    # Más compacto: menos líneas y el usuario puede ampliar si quiere
    lyrics = gr.Textbox(
        lines=7,
        label="Lyrics (puedes usar marcadores [Verse], [Chorus], etc.)",
        placeholder="[Verse]\n...\n[Chorus]\n...",
        value="[Verse]\nI love you,\nI think too much about you\n",
    )

    tags = gr.Textbox(
        lines=1,
        label="Tags (comma-separated, sin espacios)",
        placeholder="piano,ballad,romantic,slow",
        value="piano ballad",
    )

    with gr.Row():
        max_audio_length_ms = gr.Slider(5000, 240000, value=20000, step=1000, label="Max audio length (ms)")
        topk = gr.Slider(1, 200, value=50, step=1, label="Top-k")
        temperature = gr.Slider(0.1, 2.0, value=1.0, step=0.05, label="Temperature")
        cfg_scale = gr.Slider(0.0, 5.0, value=1.5, step=0.05, label="CFG scale")

    with gr.Row():
        mula_device = gr.Textbox(value="cuda", label="MuLa device (ej: cuda, cuda:0)")
        codec_device = gr.Textbox(value="cuda", label="Codec device (ej: cuda, cuda:1)")
        mula_dtype = gr.Dropdown(choices=["bf16", "fp16", "fp32"], value="bf16", label="MuLa dtype")
        codec_dtype = gr.Dropdown(choices=["fp32", "bf16", "fp16"], value="fp32", label="Codec dtype")
        lazy_load = gr.Checkbox(value=True, label="Lazy load (ahorra VRAM)")

    with gr.Row():
        save_name = gr.Textbox(value="output_ui.mp3", label="Output filename (.mp3)")
        run = gr.Button("Generar", variant="primary")

    out_audio = gr.Audio(label="Output (mp3)", type="filepath")
    out_log = gr.Textbox(lines=8, label="Log")

    run.click(
        fn=generate,
        inputs=[
            model_path,
            version,
            lyrics,
            tags,
            save_name,
            max_audio_length_ms,
            topk,
            temperature,
            cfg_scale,
            mula_device,
            codec_device,
            mula_dtype,
            codec_dtype,
            lazy_load,
        ],
        outputs=[out_audio, out_log],
    )

demo.launch(server_name="127.0.0.1", server_port=7860)
