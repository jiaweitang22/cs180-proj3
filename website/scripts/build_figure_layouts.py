"""Create responsive figure markup from the extracted, named notebook images."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "_figures"
FIGURES.mkdir(exist_ok=True)
SIZES = {entry['file']: entry['size'] for entry in json.loads((ROOT/'assets/manifest.json').read_text())['assets']}

def image(name, label, extra=""):
    width,height = SIZES[name+'.webp']
    return (f'<figure {extra}><a href="assets/{name}.webp" target="_blank" rel="noopener">'
            f'<img src="assets/{name}.webp" width="{width}" height="{height}" alt="{escape(label, quote=True)}" loading="lazy" decoding="async"></a>'
            f'<figcaption>{escape(label)}</figcaption></figure>')

def grid(items, columns=4):
    return f'<div class="result-grid cols-{columns}">\n' + '\n'.join(image(n,l) for n,l in items) + '\n</div>\n'

def write(name, body):
    (FIGURES / (name+".qmd")).write_text(body)

times=["0.25","0.50","0.75"]
write("training",grid([(f"training-{i}",l) for i,l in enumerate(["Original Half Dome", *[f"t = {t}" for t in times]])]))
write("blur",''.join(grid([(f"blur-{i}-0",f"Noisy input · t = {t}"),(f"blur-{i}-1",f"Gaussian blur · σ = {s} · t = {t}")],2) for i,(t,s) in enumerate(zip(times,[8,4,1]))))
write("one-step",''.join(grid([(f"one-step-{i}-0","Original Half Dome"),(f"one-step-{i}-1",f"Noisy input · t = {t}"),(f"one-step-{i}-2",f"One-step estimate · t = {t}")],3) for i,t in enumerate(times)))
velocity='<div class="velocity-original">'+image('half-dome-original','Original Half Dome')+'</div>\n'
for row,t in enumerate(times):
    velocity+=f'\n**t = {t}**\n\n'
    velocity+=grid([(f'velocity-{row}-{column}',label) for column,label in enumerate(['Noisy input','Predicted update','Ground-truth update','Error (RGB RMS)'])])
velocity+='<div class="error-scale"><img src="assets/velocity-error-scale.webp" alt="Shared magma error scale, from black at zero to pale yellow at 0.5" width="799" height="12"><div class="scale-ticks">'+''.join(f'<span>{t}</span>' for t in ['0','0.1','0.2','0.3','0.4','0.5'])+'</div><p>Shared RGB RMS error scale</p></div>\n'
write('velocity',velocity)
write("trajectory",grid([(f"trajectory-{i}",f"t = {t}") for i,t in enumerate(["0.50 (initial)","0.60","0.70","0.80","0.90","1.00 (final)"])],3))
write("comparison",grid([(f"comparison-{i}",l) for i,l in enumerate(["Original","Gaussian blur","One-step denoising","Euler denoising"])]))
write("conditional",grid([(f"conditional-{i}",f"Seed {180+i} · ordinary conditional") for i in range(5)]))
write("cfg-comparison",''.join(grid([(f"conditional-{i}",f"Seed {180+i} · ordinary conditional"),(f"cfg-{i}",f"Seed {180+i} · CFG w = 7")],2) for i in range(5)))
starts=["0.02","0.04","0.06","0.10","0.14","0.25","0.50"]

def editing(name, title, prompt=None):
    body=f'\n**{title}**\n\n'
    if prompt:
        body+=f'<p class="prompt"><strong>Prompt:</strong> “{escape(prompt)}”</p>\n\n'
    body+=grid([(f"{name}-{i}", l) for i,l in enumerate(["Original", *[f"Starting t = {t}" for t in starts]])])
    return body

write("edit-photos",''.join(editing("edit-"+n,t) for n,t in [("campanile","Campanile"),("half-dome","Half Dome"),("chicken","Pixel-art chicken")]))
write("edit-drawings",''.join(editing("edit-"+n,t) for n,t in [("web-landscape","Web image: acrylic landscape"),("drawing-mountain","My drawing: snow-capped mountain"),("drawing-flower","My drawing: flower")]))
write("text-edits",''.join(editing("text-edit-"+n,t,p) for n,t,p in [
    ("campanile","Campanile → lighthouse","a photograph of a lighthouse beside the ocean"),
    ("half-dome","Half Dome → volcano","a photograph of an erupting volcano surrounded by forest"),
    ("chicken","Pixel chicken → rooster","a photograph of a rooster against a turquoise background")]))

anagrams=''
for name,title,a,b in [
    ("waterfall-sailor","Waterfall / sailor","an oil painting of a canyon waterfall","an oil painting of a bearded sailor"),
    ("cabin-wolf","Cabin / wolf","an oil painting of a snow-covered cabin in pine trees","an oil painting of a wolf's face")]:
    anagrams+=f'\n**{title}**\n\n<div class="result-grid cols-2">\n'
    anagrams+=image(f"anagram-{name}-0",f"Upright: {a}",f'class="anagram-view" id="{name}"')+'\n'
    anagrams+=image(f"anagram-{name}-1",f"Rotated 180°: {b}")+'\n</div>\n'
    anagrams+=f'<button class="rotate-result" aria-controls="{name}" aria-pressed="false">Rotate 180°</button>\n'
write("anagrams",anagrams)

hybrids=''
for name,title,a,b in [
    ("fox-forest","Fox / autumn forest","an oil painting of a fox","an oil painting of an autumn forest"),
    ("elephant-ruins","Elephant / stone ruins","an oil painting of an elephant's face","an oil painting of ancient stone ruins")]:
    hybrids+=f'\n**{title}**\n\n<p class="prompt"><strong>Distant:</strong> “{escape(a)}”<br><strong>Close:</strong> “{escape(b)}”</p>\n\n'
    hybrids+=f'<div class="hybrid-grid"><figure><a href="assets/hybrid-{name}.webp" target="_blank" rel="noopener"><img class="hybrid-full" src="assets/hybrid-{name}.webp" width="512" height="512" alt="{escape(title)} hybrid, full view" loading="lazy"></a><figcaption>Full hybrid · close view</figcaption></figure><figure><div class="distant-frame">'
    for size in [64,32]:
        hybrids+=f'<figure><img src="assets/hybrid-{name}-{size}.webp" width="{size}" height="{size}" alt="{escape(title)} hybrid at {size} pixels" loading="lazy"><figcaption>{size} × {size} px</figcaption></figure>'
    hybrids+='</div><figcaption>Native thumbnails · distant views</figcaption></figure></div>\n'
write("hybrids",hybrids)
print("Built 13 figure layouts.")
