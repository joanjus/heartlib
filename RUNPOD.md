# HeartMuLa en RunPod – Guía reproducible y definitiva

Este documento describe el procedimiento correcto y reproducible para ejecutar HeartMuLa desde este fork en RunPod, evitando problemas conocidos de almacenamiento, caché y descarga de modelos en entornos con GPU cloud.

Si este documento se sigue en orden, el entorno funciona.
Si se ignora, los errores habituales reaparecen.

## 1. Requisitos del Pod

Configuración recomendada y validada:

- GPU: NVIDIA A40 con 48 GB de VRAM o equivalente
- RAM: mínimo 32 GB
- Storage: mínimo 60 GB, recomendado 80 GB
- Sistema operativo: Linux, imagen base estándar de RunPod

El sistema raíz es limitado. Todo el almacenamiento pesado debe residir en la ruta workspace.

## 2. Advertencia crítica sobre Hugging Face

No usar en RunPod ni en contenedores:

- hf download
- descargas basadas en enlaces simbólicos
- rutas de caché por defecto

Motivos:

- hf download crea enlaces simbólicos incompatibles con modelos grandes
- la caché por defecto usa el sistema raíz limitado
- los errores habituales son archivos faltantes y errores de cuota de disco

Conclusión:

En RunPod es obligatorio controlar explícitamente las rutas de caché y el método de descarga.

## 3. Configuración obligatoria de rutas

Antes de instalar dependencias o descargar modelos, ejecutar:

    export HF_HOME=/workspace/.cache/huggingface
    export TRANSFORMERS_CACHE=/workspace/.cache/huggingface
    export HF_DATASETS_CACHE=/workspace/.cache/huggingface
    export TMPDIR=/workspace/tmp
    mkdir -p /workspace/.cache
    mkdir -p /workspace/tmp

## 4. Clonado del repositorio

    git clone https://github.com/joanjus/heartlib.git
    cd heartlib

## 5. Instalación del entorno

    conda env create -f environment.yml
    conda activate heartmula
    pip install -e .

Si aparecen errores por dependencias faltantes, deben instalarse explícitamente en este entorno.

## 6. Descarga correcta de modelos

La descarga debe realizarse desde Python usando snapshot_download y forzando archivos reales.

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id="HeartMuLa/HeartMuLaGen",
        local_dir="/workspace/ckpt",
        local_dir_use_symlinks=False
    )

## 7. Estructura esperada de los modelos

La estructura final debe ser exactamente la siguiente:

    /workspace/ckpt/
    ├── HeartCodec-oss/
    ├── HeartMuLa-oss-3B/
    ├── gen_config.json
    └── tokenizer.json

Si esta estructura no existe, el modelo no cargará.

## 8. Test mínimo por línea de comandos

    python examples/run_music_generation.py --model_path=/workspace/ckpt --version=3B

Si este comando funciona, el entorno es válido.

## 9. Interfaz gráfica

    python app_gradio.py

## 10. Principios operativos

- Todo el almacenamiento pesado debe ir a workspace
- Nunca usar hf download en contenedores
- Validar siempre la estructura real de los modelos
- Probar primero por línea de comandos
- La interfaz gráfica es un paso posterior

## 11. Nota final

Este procedimiento es reproducible incluso si el Pod se elimina y se crea de nuevo. Seguir este documento es obligatorio para evitar errores ya conocidos.
