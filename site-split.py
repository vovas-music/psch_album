"""Split PSCHPTHY and Normal for the site where this album hands one to the other.

    python3 site-split.py <psch_1.flac> <normal.flac> 7_psch.flac 8_normal.flac <out-dir>

`psch_1.flac` and `normal.flac` are the songs' masters, from vovas-music/psch
and vovas-music/normal. The other two are this repository's renders, which
are bit-exact copies of those masters placed on whole samples: 7_psch.flac is
the project's [1165 s, 1440 s], 8_normal.flac its [1440 s, 1687 s]. Counted
from 1165 s, at 44.1 kHz, psch_album.RPP puts
  - psch at sample 34383;
  - Normal's item at 12206380, its file trimmed by 1448 samples (SOFFS);
  - psch's end at 12233430, so the two cross-fade over 27050 samples.

Writes psch.flac, psch to the sample where Normal enters, and normal.flac,
opening on the album's own crossfade and then Normal's master to its end.
Outside the crossfade every sample is the master's, and the two files played
back to back are the album's samples over the same span.
"""

import subprocess
import sys

import numpy as np

SR = 44100
PSCH_AT, NORMAL_AT, PSCH_END, SOFFS = 34383, 12206380, 12233430, 1448


def load(path):
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-'],
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).reshape(-1, 2)


def save(samples, path):
    subprocess.run(
        ['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ac', '2', '-ar', str(SR),
         '-i', '-', '-c:a', 'flac', '-compression_level', '8', path],
        input=samples.tobytes(),
        check=True,
    )


def main(psch_path, normal_path, render_7, render_8, out):
    psch, normal = load(psch_path), load(normal_path)
    album = np.concatenate([load(render_7), load(render_8)])
    crossfade = PSCH_END - NORMAL_AT

    new_psch = psch[: NORMAL_AT - PSCH_AT]
    new_normal = np.concatenate(
        [album[NORMAL_AT:PSCH_END], normal[SOFFS + crossfade :]]
    )

    if not np.array_equal(album[PSCH_AT:NORMAL_AT], new_psch):
        sys.exit('psch differs from the album render: not the master it was made from')
    span = min(len(album) - PSCH_END, len(new_normal) - crossfade) - SR
    if not np.array_equal(
        album[PSCH_END : PSCH_END + span], new_normal[crossfade : crossfade + span]
    ):
        sys.exit('Normal differs from the album render: not the master it was made from')

    save(new_psch, f'{out}/psch.flac')
    save(new_normal, f'{out}/normal.flac')


if __name__ == '__main__':
    main(*sys.argv[1:6])
