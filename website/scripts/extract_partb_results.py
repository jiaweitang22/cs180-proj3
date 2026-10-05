"""Export saved Part B figures and provenance without executing the notebook.

Run with Python + Pillow + NumPy from the repository root. Keep the original
plot in a lossless WebP; remove only titles/margins from sample-grid views.
Part A's extraction script, figures, and manifest are independent.
"""
import base64
import hashlib
import io
import json
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/partb.ipynb"
ASSETS = ROOT / "website/assets/partb"
FIGURES = ROOT / "website/_figures/partb"

# Zero-based cell/output indices in the provided, executed notebook.
# Titles and explicit PNG checks make a changed cell layout fail visibly.
SPECS = [
    ("noise-levels", 14, 0, "Noise levels by row", "Noise levels by row, top to bottom: σ = 0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0. Each column reuses the same test digit and noise tensor.", True),
    ("denoise-loss", 21, 0, "loss_plot(train_losses", "Single-step denoising training MSE over all five epochs. Faint line: every optimizer step; solid line: 100-step moving average.", False),
    ("denoise-epoch1", 21, 1, "denoise, epoch", "Epoch 1 · σ = 0.5 · Rows: clean test digits / noisy inputs / predictions.", True),
    ("denoise-epoch5", 21, 2, "denoise, epoch", "Epoch 5 · σ = 0.5 · Rows: clean test digits / the same noisy inputs / predictions.", True),
    ("denoise-ood", 23, 0, "sigma by column", "Same test digit at every noise level. Columns: σ = 0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0. Rows: noisy input / prediction.", True),
    ("pure-noise-loss", 25, 0, "loss_plot(pure_losses", "Pure-noise denoiser training MSE over five epochs. Faint line: every optimizer step; solid line: 100-step moving average.", False),
    ("pure-noise-samples", 25, 1, "Pure-noise predictions", "Pure-noise predictions · Top row: epoch 1; bottom row: epoch 5. Both checkpoints use the same ten noise inputs.", True),
    ("time-loss", 35, 1, "loss_plot(time_losses", "Time-conditioned flow training MSE over ten epochs. Faint line: every optimizer step; solid line: 100-step moving average.", False),
    ("time-epoch1", 37, 0, "Time-conditioned flow matching", "Epoch 1 · Time conditioning only · 40 samples · 50 Euler steps · Seed 180.", True),
    ("time-epoch5", 37, 1, "Time-conditioned flow matching", "Epoch 5 · Time conditioning only · Same 40 initial noise samples and 50 Euler steps.", True),
    ("time-epoch10", 37, 2, "Time-conditioned flow matching", "Epoch 10 · Time conditioning only · Same 40 initial noise samples and 50 Euler steps.", True),
    ("class-loss", 44, 1, "loss_plot(class_losses", "Class-conditioned flow training MSE over ten epochs. Faint line: every optimizer step; solid line: 100-step moving average.", False),
    ("no-scheduler-loss", 44, 3, "loss_plot(no_scheduler_losses", "Class-conditioned training without a scheduler · Constant Adam learning rate 0.003 · Ten epochs.", False),
    ("class-epoch1", 46, 0, "Class-conditioned, epoch", "Epoch 1 · Columns: requested digits 0–9; four instances per digit · CFG γ = 5 · 300 Euler steps · Seed 180.", True),
    ("class-epoch5", 46, 1, "Class-conditioned, epoch", "Epoch 5 · Columns: requested digits 0–9; four instances per digit · Same noise, CFG, and Euler steps.", True),
    ("class-epoch10", 46, 2, "Class-conditioned, epoch", "Epoch 10 · Columns: requested digits 0–9; four instances per digit · Same noise, CFG, and Euler steps.", True),
    ("no-scheduler-epoch10", 46, 3, "No scheduler, epoch 10", "No scheduler · Epoch 10 · Constant learning rate 0.003 · Columns: digits 0–9; four instances per digit · CFG γ = 5.", True),
    ("scheduler-comparison", 46, 4, "Epoch 10: scheduled", "Epoch 10 comparison · Top four rows: exponential scheduler; bottom four rows: constant learning rate 0.003. Columns: digits 0–9. Identical initial noise, CFG γ = 5, and 300 Euler steps.", True),
]


def main():
    notebook_bytes = NOTEBOOK.read_bytes()
    notebook = json.loads(notebook_bytes)
    # Validate every selection before changing any exported figures.
    selected = []
    for name, cell, output, marker, caption, crop_grid in SPECS:
        source = "".join(notebook["cells"][cell]["source"])
        if marker not in source:
            raise ValueError(f"Notebook layout changed for {name}: cell {cell}")
        data = notebook["cells"][cell]["outputs"][output]["data"]["image/png"]
        image = Image.open(io.BytesIO(base64.b64decode("".join(data)))).convert("RGB")
        selected.append((name, cell, output, caption, crop_grid, image))

    ASSETS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "notebook": "notebooks/partb.ipynb",
        "sha256": hashlib.sha256(notebook_bytes).hexdigest(),
        "indices": "zero-based cell and output indices",
        "assets": [],
    }
    for name, cell, output, caption, crop_grid, image in selected:
        original_name = f"{name}-original.webp"
        image.save(ASSETS / original_name, lossless=True)
        crop = None
        if crop_grid:
            # make_grid has a black canvas. Locate that canvas, excluding the
            # small black title above it, without touching any digit pixels.
            pixels = np.asarray(image)
            dark = np.max(pixels, axis=2) < 32
            ys = np.flatnonzero(dark.mean(axis=1) > 0.30)
            if not len(ys):
                raise ValueError(f"No sample-grid canvas found for {name}")
            y0, y1 = int(ys[0]), int(ys[-1]) + 1
            xs = np.flatnonzero(dark[y0:y1].mean(axis=0) > 0.30)
            x0, x1 = int(xs[0]), int(xs[-1]) + 1
            crop = [x0, y0, x1, y1]
            image = image.crop(crop)
        display_name = f"{name}.webp"
        image.save(ASSETS / display_name, lossless=True)
        manifest["assets"].append({
            "file": display_name, "original": original_name,
            "cell": cell, "output": output, "size": list(image.size),
            "crop": crop, "caption": caption,
        })
        width, height = image.size
        markup = (
            '<figure class="mnist-figure">\n'
            f'<a href="assets/partb/{original_name}" target="_blank" rel="noopener" '
            f'aria-label="Open original notebook figure: {escape(caption, quote=True)}">\n'
            f'<img src="assets/partb/{display_name}" width="{width}" height="{height}" '
            f'alt="{escape(caption, quote=True)}" loading="lazy" decoding="async">\n'
            '</a>\n'
            f'<figcaption>{escape(caption)}</figcaption>\n'
            '</figure>\n'
        )
        (FIGURES / f"{name}.qmd").write_text(markup)
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Exported {len(selected)} saved Part B figures and their original plots.")


if __name__ == "__main__":
    main()
