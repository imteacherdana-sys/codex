"""v3 mix: two 30s Kling clips, ElevenLabs dub placed on Kling's own speech segments, no subtitles."""
import json, os, subprocess, sys

D = sys.argv[1]
clipA, clipB = sys.argv[2], sys.argv[3]
plan = json.load(open(sys.argv[4]))  # {"A": [[line, start, target_len], ...], "B": [...], "muteA": [[s,e],...], "muteB": [...]}
out = sys.argv[5]


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


LA = dur(clipA)
END = LA + dur(clipB)
inputs = ['-i', clipA, '-i', clipB]
fc = ['[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[vc][ac]',
      f'[vc]fade=t=out:st={END - 0.35:.2f}:d=0.35[vout]']
mutes = [(s, e) for s, e in plan['muteA']] + [(s + LA, e + LA) for s, e in plan['muteB']]
expr = '+'.join(f'between(t,{max(0, s - 0.12):.2f},{e + 0.12:.2f})' for s, e in mutes) or '0'
fc.append(f"[ac]volume='0.8*(1-gt({expr},0))':eval=frame[amb]")
labels, log = [], []
idx = 2
for key, off in (('A', 0.0), ('B', LA)):
    for line, start, target in plan[key]:
        f = os.path.join(D, 'el', f'{line}.wav')
        d = dur(f)
        tempo = 1.0 if not target else min(1.15, max(0.9, d / target))
        st = off + start
        inputs += ['-i', f]
        ms = int(st * 1000)
        fc.append(f'[{idx}:a]' + (f'atempo={tempo:.3f},' if abs(tempo - 1) > 0.005 else '') +
                  f'adelay={ms}|{ms},volume=1.7[d{idx}]')
        labels.append(f'[d{idx}]')
        log.append(f'{line}: {st:6.2f}-{st + d / tempo:6.2f}s tempo {tempo:.2f}')
        idx += 1
inputs += ['-i', os.path.join(D, 'sfx.wav'), '-i', os.path.join(D, 'bgm.wav')]
fc.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0,asplit=2[dia][sc]')
fc.append(f'[{idx + 1}:a]volume=0.5[bg]')
fc.append('[bg][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[bgd]')
fc.append(f'[{idx}:a]volume=0.7[fx]')
fc.append('[dia][fx][bgd][amb]amix=inputs=4:normalize=0,alimiter=limit=0.95[aout]')
cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
       '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
       '-t', f'{END:.3f}', '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
print('\n'.join(log))
