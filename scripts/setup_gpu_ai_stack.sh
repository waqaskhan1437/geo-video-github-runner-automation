#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$PWD/.ai-stack}"
COMFY_DIR="${ROOT_DIR}/ComfyUI"
VENV_DIR="${COMFY_DIR}/.venv"
CUSTOM_NODES_DIR="${COMFY_DIR}/custom_nodes"

echo "[setup] root: ${ROOT_DIR}"
mkdir -p "${ROOT_DIR}"

if [[ ! -d "${COMFY_DIR}" ]]; then
  echo "[setup] cloning ComfyUI..."
  git clone https://github.com/comfyanonymous/ComfyUI.git "${COMFY_DIR}"
else
  echo "[setup] ComfyUI already exists, pulling latest..."
  git -C "${COMFY_DIR}" pull --ff-only
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r "${COMFY_DIR}/requirements.txt"
python -m pip install huggingface_hub

mkdir -p "${CUSTOM_NODES_DIR}"

if [[ ! -d "${CUSTOM_NODES_DIR}/ComfyUI-Manager" ]]; then
  git clone https://github.com/ltdrdata/ComfyUI-Manager.git "${CUSTOM_NODES_DIR}/ComfyUI-Manager"
else
  git -C "${CUSTOM_NODES_DIR}/ComfyUI-Manager" pull --ff-only
fi

if [[ ! -d "${CUSTOM_NODES_DIR}/ComfyUI-VideoHelperSuite" ]]; then
  git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "${CUSTOM_NODES_DIR}/ComfyUI-VideoHelperSuite"
else
  git -C "${CUSTOM_NODES_DIR}/ComfyUI-VideoHelperSuite" pull --ff-only
fi

if [[ "${DOC_INSTALL_OPEN_SOURCE_EDITOR:-1}" == "1" ]]; then
  python -m pip install moviepy opencv-python-headless
fi

cat <<'TXT'
[setup] GPU AI stack ready.
Next steps on runner:
  1) Activate venv: source .ai-stack/ComfyUI/.venv/bin/activate
  2) Launch ComfyUI: python .ai-stack/ComfyUI/main.py --listen 0.0.0.0 --port 8188
  3) Import Wan/CogVideoX workflow JSON via ComfyUI UI or API.
TXT

