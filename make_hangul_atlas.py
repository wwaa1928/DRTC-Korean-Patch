"""Generate a Galmuri11 Hangul overlay, or merge it into a downloaded atlas.
Requires Pillow. With --base, all other Unicode cells retain their pixels.
"""
from pathlib import Path
import argparse, hashlib, json
import sys
sys.dont_write_bytecode=True
from PIL import Image


def read_bdf(path):
    glyphs = {}
    current = None
    bitmap = False
    for line in path.read_text('utf-8').splitlines():
        if line.startswith('STARTCHAR '):
            current = {'rows': []}
            bitmap = False
        elif line.startswith('ENCODING '):
            current['codepoint'] = int(line.split()[1])
        elif line.startswith('BBX '):
            current['box'] = tuple(map(int, line.split()[1:]))
        elif line == 'BITMAP':
            bitmap = True
        elif line == 'ENDCHAR':
            glyphs[current['codepoint']] = current
            current = None
            bitmap = False
        elif bitmap:
            current['rows'].append(line)
    return glyphs


def build(base, bdf, output, baseline=12):
    if base and base.resolve() == output.resolve():
        raise ValueError('Output must be a separate copy of the base atlas.')
    original = Image.open(base).convert('RGBA') if base else Image.new('RGBA',(3072,3072))
    if original.size != (3072, 3072):
        raise ValueError('Expected the 3072x3072 V202.0 atlas.')
    im = original.copy()
    glyphs = read_bdf(bdf)
    codepoints = list(range(0xac00,0xd7a4)) + list(range(0x3131,0x318f))
    missing, clipped = [], []
    visible = 0
    for cp in codepoints:
        g = glyphs.get(cp)
        if not g:
            missing.append(cp)
            continue
        w,h,dx,dy = g['box']
        x,y=(cp&255)*12,(cp>>8)*12
        tile = Image.new('RGBA',(12,12))
        top = baseline-dy-h
        for rowno,row in enumerate(g['rows']):
            bits = int(row,16)
            nbits=len(row)*4
            for col in range(w):
                if bits & (1<<(nbits-1-col)):
                    px,py=dx+col,top+rowno
                    if not (0<=px<12 and 0<=py<12):
                        clipped.append(cp)
                    else:
                        tile.putpixel((px,py),(255,255,255,255))
        visible += bool(tile.getchannel('A').getbbox())
        im.paste(tile,(x,y))
    if missing or clipped:
        raise ValueError(f'Missing: {missing}; clipped: {sorted(set(clipped))}')
    # Erase the changed cells in both images and compare everything else.
    lhs,rhs=original.copy(),im.copy()
    blank=Image.new('RGBA',(12,12))
    for cp in codepoints:
        xy=((cp&255)*12,(cp>>8)*12)
        lhs.paste(blank,xy);rhs.paste(blank,xy)
    assert lhs.tobytes()==rhs.tobytes()
    output.parent.mkdir(parents=True,exist_ok=True)
    im.save(output)
    result={'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest() if base else None,
            'bdf_sha256':hashlib.sha256(bdf.read_bytes()).hexdigest(),
            'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'size':list(im.size),'mode':'RGBA','baseline_in_cell':baseline,
            'hangul_syllables':11172,'compatibility_jamo':94,
            'visible_added_cells':visible,'all_other_cells_preserved':True,
            'clipped_glyphs':0,'missing_glyphs':0}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,help='Optional user-downloaded atlas; omit for Hangul-only overlay.')
    p.add_argument('--bdf',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--baseline',type=int,default=12)
    a=p.parse_args()
    print(json.dumps(build(a.base,a.bdf,a.output,a.baseline),indent=2))
