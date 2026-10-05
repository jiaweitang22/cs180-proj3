"""Extract saved notebook outputs; never evaluate the model or alter the notebook.

Run with Python + Pillow + NumPy from the repository root.
Figure crops remove only Matplotlib margins/titles; HTML supplies readable labels.
"""
import base64
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/parta.ipynb"
ASSETS = ROOT / "website/assets"
ASSETS.mkdir(parents=True, exist_ok=True)
notebook_bytes = NOTEBOOK.read_bytes()
notebook = json.loads(notebook_bytes)
manifest = {"notebook": "notebooks/parta.ipynb", "sha256": hashlib.sha256(notebook_bytes).hexdigest(), "assets": []}

def read_image(cell, output):
    data = notebook["cells"][cell]["outputs"][output]["data"]["image/png"]
    return Image.open(io.BytesIO(base64.b64decode("".join(data)))).convert("RGB")

def save(image, name, cell, output, crop=None):
    target = ASSETS / (name + ".webp")
    if not target.exists() or not np.array_equal(np.asarray(Image.open(target).convert("RGB")), np.asarray(image)):
        image.save(target, lossless=True)
    manifest["assets"].append({"file": name + ".webp", "cell": cell, "output": output,
                               "size": list(image.size), "crop": crop})

def runs(values):
    edges = np.diff(np.r_[False, values, False].astype(int))
    return list(zip(np.where(edges == 1)[0], np.where(edges == -1)[0]))

def image_runs(values):
    # Tiny near-white streaks inside a picture are not Matplotlib gutters.
    groups = runs(values)
    merged = []
    for a,b in groups:
        if merged and a-merged[-1][1] <= 12:
            merged[-1] = (merged[-1][0],b)
        else:
            merged.append((a,b))
    return [(a,b) for a,b in merged if b-a > 100]

def panel(cell, output, name, columns, rows=1, count=None):
    image = read_image(cell, output)
    save(image, name + "-panel", cell, output)
    pixels = np.asarray(image)
    first_y = round(.5 * image.height / rows)
    column_runs = image_runs(np.any(pixels[first_y] < 240, axis=1))
    # Plot images share equal axes. Infer their layout from the widest pictures
    # so a white portrait background is retained rather than cropped away.
    width = max(b-a for a,b in column_runs)
    templates = [(round(((a+b)/2)/image.width*columns-.5), (a+b)/2)
                 for a,b in column_runs if b-a >= width-6]
    if len(templates) >= 2:
        slope, intercept = np.polyfit([c for c,_ in templates], [x for _,x in templates],1)
    else:
        slope = image.width / columns
        intercept = templates[0][1] - templates[0][0]*slope
    column_runs = [(round(intercept+c*slope-width/2),round(intercept+c*slope+width/2)) for c in range(columns)]
    for row in range(rows):
        y = round((row + .5) * image.height / rows)
        x_runs = column_runs
        if len(x_runs) != columns and not (count and row == rows-1):
            raise ValueError(f"Unexpected panel geometry: {name}, row {row}: {x_runs}")
        for column, (x0,x1) in enumerate(x_runs):
            i = row * columns + column
            if count is not None and i >= count:
                continue
            # The supplied panel() uses equal square axes in 400-pixel rows,
            # with a ten-pixel bottom margin in its tight notebook rendering.
            # Derive vertical bounds from axes width, preserving white scenery.
            row_stride = (image.height-11)/rows
            y1 = round(image.height-10-(rows-1-row)*row_stride)
            y0 = y1-width+1
            crop = [int(x0),int(y0),int(x1),int(y1)]
            if abs((x1-x0)-(y1-y0)) > 8:
                raise ValueError(f"Non-square panel: {name}, {i}, {crop}")
            save(image.crop(crop), f"{name}-{i}", cell, output, crop)

save(read_image(9,0), "half-dome-original", 9,0)
panel(11,0,"training",4)
for k in range(3):
    panel(13,k,f"blur-{k}",2)
    panel(15,k+1,f"one-step-{k}",3)
save(read_image(18,0),"velocity",18,0)
panel(20,0,"trajectory",3,2)
panel(20,1,"comparison",4)
panel(22,0,"conditional",4,2,5)
panel(26,0,"cfg",4,2,5)
for k, name in enumerate(["campanile","half-dome","chicken"]):
    panel(30,2*k,"edit-"+name,4,2)
    panel(34,2*k,"text-edit-"+name,4,2)
for k,name in enumerate(["web-landscape","drawing-mountain","drawing-flower"]):
    panel(32,2*k,"edit-"+name,4,2)
for cell,output,name in [(37,0,"waterfall-sailor"),(38,0,"cabin-wolf")]:
    panel(cell,output,"anagram-"+name,2)
for cell,output,name in [(41,1,"fox-forest"),(42,1,"elephant-ruins")]:
    im=read_image(cell,output)
    save(im,"hybrid-"+name,cell,output)
    save(read_image(cell,output+2),"hybrid-"+name+"-64",cell,output+2)
    save(im.resize((32,32),Image.Resampling.LANCZOS),"hybrid-"+name+"-32",cell,output)
(ASSETS / "manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(f"Extracted {len(manifest['assets'])} assets from the saved notebook.")
