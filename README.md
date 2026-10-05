# CS180 Project 3

## Project webpage

[Published Part A report](https://jiaweitang22.github.io/cs180-proj3/)

The webpage uses Quarto 1.7.32, the Bootstrap-based Cosmo theme, and MathJax,
matching the stack of the supplied student reference. Edit `website/index.qmd`
for explanations and `website/styles.css` for layout. Figure markup lives in
`website/_figures/`; named results and their notebook provenance are in
`website/assets/manifest.json`.

With [Quarto](https://quarto.org/docs/get-started/) installed:

```sh
quarto preview website
quarto render website
```

Pushing website changes to `main` automatically renders the report and deploys
GitHub Pages through `.github/workflows/pages.yml`. Model execution is disabled
during rendering: the page displays saved results rather than rerunning PixNerd.
The public repository contains the webpage source and selected result assets.
The local research notebook and support files are not included in this website
deployment.

To refresh figures after a notebook run, use Python with Pillow and NumPy:

```sh
python website/scripts/extract_results.py
python website/scripts/build_figure_layouts.py
quarto render website
```

The extraction script targets the current notebook's cell/output positions;
update them if cells are inserted or moved. It preserves the original images,
removes plot margins for responsive grids, and makes native distant-view
thumbnails for the hybrids. It never edits or executes the notebook.

For the Gradescope website PDF, use the browser's Print / Save as PDF after
the page and equations have loaded. Print styling preserves both views of
each illusion and removes navigation controls. Submit code separately.

## Local experiment workspace

```text
notebooks/  Working notebook (parta.ipynb) and untouched starter (parta_updated.ipynb)
images/     All input images, including the supplied course examples
outputs/    Generated images, figures, tensors, and metrics, grouped by run
src/        Supplied model adapter, setup, and PixNerd implementation
```

Open `notebooks/parta.ipynb` to work on Part A. Student exercise functions stay
in the notebook. Set your image paths relative to the project root, for example
`images/my_photo.jpg`, and fill in the editing prompts.

The notebook finds the project root when launched from the root or `notebooks/`.
Each run saves results under `outputs/<timestamp>-<id>/`. Existing support-code
edits are preserved when setup runs.

For Colab or Kaggle, upload the working notebook alone and run setup on a CUDA
GPU (preferably A100). Its embedded support files keep standalone uploads working.
Upload your own images separately and set their runtime paths. Save the executed
notebook and download your results before disconnecting.

For a local CUDA machine, install `requirements.txt` with a CUDA-compatible
PyTorch/torchvision installation first. Apple MPS support has not been added.
The working notebook contains the completed Part A exercise functions and saved
model outputs.

`.gitignore` excludes generated research outputs, the rendered website, and model
caches. The selected website assets are tracked separately under `website/`.

[Project overview](https://cal-cs180.github.io/fa26/hw/proj3-flow/index.html) ·
[Part A instructions](https://cal-cs180.github.io/fa26/hw/proj3-flow/parta.html)

Due October 20, 2026. Submit Part A code and webpage PDF to Gradescope.
