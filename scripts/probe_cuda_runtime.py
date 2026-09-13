"""Write a portable CUDA/PyTorch/cuGraph availability receipt."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def optional_torch_details() -> dict[str, object]:
    """Return torch CUDA details without making torch a base dependency."""
    if importlib.util.find_spec("torch") is None:
        return {"torch_available": False, "torch_cuda_available": False}
    import torch

    return {
        "torch_available": True,
        "torch_version": torch.__version__,
        "torch_cuda_available": torch.cuda.is_available(),
        "torch_cuda_version": torch.version.cuda,
        "torch_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        nvidia_smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        nvidia_smi = None
    payload = {
        "schema_version": "1.0", "captured_at": datetime.now(UTC).isoformat(), "platform": platform.platform(),
        "cugraph_available": importlib.util.find_spec("cugraph") is not None,
        "cuda_runtime_available": nvidia_smi is not None and nvidia_smi.returncode == 0,
        "nvidia_smi": nvidia_smi.stdout.strip() if nvidia_smi and nvidia_smi.returncode == 0 else None,
        **optional_torch_details(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
