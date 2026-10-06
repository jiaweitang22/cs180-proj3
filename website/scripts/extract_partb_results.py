"""Export saved Part B figures and provenance without executing the notebook.

Run with Python + Pillow from the repository root. Export complete lossless
figures so titles, row labels, and column labels remain visible.
Part A's extraction script, figures, and manifest are independent.
"""
import base64
import hashlib
import io
import json
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/partb.ipynb"
ASSETS = ROOT / "website/assets/partb"
FIGURES = ROOT / "website/_figures/partb"

# Zero-based cell/output indices in the provided, executed notebook.
# Titles and explicit PNG checks make a changed cell layout fail visibly.
SPECS = [
    ("noise-levels", 14, 0, "MNIST at Different Noise Levels", "MNIST at increasing noise levels."),
    ("denoise-loss", 21, 0, "loss_plot(train_losses", "Single-step denoising training MSE over all five epochs. Faint line: every optimizer step; solid line: 100-step moving average."),
    ("denoise-epoch1", 21, 1, "Denoising — Epoch", "Denoising · Epoch 1."),
    ("denoise-epoch5", 21, 2, "Denoising — Epoch", "Denoising · Epoch 5."),
    ("denoise-ood", 23, 0, "Denoising at Different Noise Levels", "The same digit at seven noise levels."),
    ("pure-noise-loss", 25, 0, "loss_plot(pure_losses", "Pure-noise denoiser training MSE over five epochs. Faint line: every optimizer step; solid line: 100-step moving average."),
    ("pure-noise-epoch1", 25, 1, "Pure-noise Predictions", "Pure-noise predictions · Epoch 1."),
    ("pure-noise-epoch5", 25, 2, "Pure-noise Predictions", "Pure-noise predictions · Epoch 5."),
    ("time-loss", 35, 1, "loss_plot(time_losses", "Time-conditioned flow training MSE over ten epochs. Faint line: every optimizer step; solid line: 100-step moving average."),
    ("time-epoch1", 37, 0, "Time-conditioned Samples", "Time conditioning · Epoch 1."),
    ("time-epoch5", 37, 1, "Time-conditioned Samples", "Time conditioning · Epoch 5."),
    ("time-epoch10", 37, 2, "Time-conditioned Samples", "Time conditioning · Epoch 10."),
    ("class-loss", 44, 1, "loss_plot(class_losses", "Class-conditioned flow training MSE over ten epochs. Faint line: every optimizer step; solid line: 100-step moving average."),
    ("no-scheduler-loss", 44, 3, "loss_plot(no_scheduler_losses", "Class-conditioned training without a scheduler · Constant Adam learning rate 0.003 · Ten epochs."),
    ("class-epoch1", 46, 0, "Class-conditioned Samples", "Class conditioning · Epoch 1."),
    ("class-epoch5", 46, 1, "Class-conditioned Samples", "Class conditioning · Epoch 5."),
    ("class-epoch10", 46, 2, "Class-conditioned Samples", "Class conditioning · Epoch 10."),
    ("no-scheduler-epoch10", 46, 3, "No Scheduler — Epoch 10", "No scheduler · Epoch 10."),
]


def main():
    notebook_bytes = NOTEBOOK.read_bytes()
    notebook = json.loads(notebook_bytes)
    # Validate every selection before changing any exported figures.
    selected = []
    for name, cell, output, marker, caption in SPECS:
        source = "".join(notebook["cells"][cell]["source"])
        if marker not in source:
            raise ValueError(f"Notebook layout changed for {name}: cell {cell}")
        data = notebook["cells"][cell]["outputs"][output]["data"]["image/png"]
        image = Image.open(io.BytesIO(base64.b64decode("".join(data)))).convert("RGB")
        selected.append((name, cell, output, caption, image))

    ASSETS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "notebook": "notebooks/partb.ipynb",
        "sha256": hashlib.sha256(notebook_bytes).hexdigest(),
        "indices": "zero-based cell and output indices",
        "assets": [],
    }
    for name, cell, output, caption, image in selected:
        original_name = f"{name}-original.webp"
        image.save(ASSETS / original_name, lossless=True)
        display_name = f"{name}.webp"
        image.save(ASSETS / display_name, lossless=True)
        manifest["assets"].append({
            "file": display_name, "original": original_name,
            "cell": cell, "output": output, "size": list(image.size),
            "caption": caption,
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
