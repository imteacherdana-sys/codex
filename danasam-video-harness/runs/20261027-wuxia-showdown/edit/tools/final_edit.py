"""단아쌤 얼굴 녹화본으로 최종 편집본을 만든다 (A안: 말하는 장면은 얼굴 크게, 나머지는 오른쪽 아래 작은 창).

1) plan  : 편집표(voice_edl.py)로 장면 길이를 정해 assets/face/durs.json에 쓴다.
           이 길이로 build.py를 다시 돌리고(DURS=…), 렌더보다 길어진 장면만 다시 렌더링한다.
2) build : 장면마다 화면 + 얼굴 + 목소리를 붙이고, 배경음악·효과음·자막을 얹어 out/에 완성본을 만든다.

사용: python3 tools/final_edit.py plan
      python3 tools/final_edit.py build [720|1080]
"""
import json
import subprocess
import sys
import wave
from pathlib import Path
from statistics import median

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voice_edl import EDL  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FACE = ROOT / "assets/face/face_all.mp4"
WORK = ROOT / "out/final_work"
SR = 48000
LEAD, GAP, TAIL = 0.35, 0.22, 0.45
PAD_IN, PAD_OUT = 0.06, 0.10
CLIP_MIN = 8.6
FULL_KINDS = {"talk"}
FULL_NAMES = {"authority"}
NO_FACE = {"film"}
# 8개 그리드는 작은 얼굴 창이 8번 칸을 가려서 목소리만 쓴다. 표·그래프 장면은 얼굴 창을 오른쪽 위에 둔다
VOICE_ONLY = {"grid"}
PIP_TOP = {"credits", "board"}

transcript = json.loads((ROOT / "assets/face/transcript.json").read_text())["segments"]
track = json.loads((ROOT / "assets/face/track.json").read_text())


def run(cmd):
    subprocess.run(cmd, check=True)


def pieces_of(name):
    """장면의 [(원본 시작, 원본 끝, 자막)] — 말소리 구간 그대로 (앞뒤 여유 없음)."""
    out = []
    for ref, text in EDL.get(name, []):
        if isinstance(ref, tuple):
            i, a, b = ref
        else:
            i = ref
            a, b = transcript[i]["start"] - PAD_IN, transcript[i]["end"] + PAD_OUT
        out.append((a, b, text))
    return out


def source_cuts(name):
    """장면에 쓸 원본 구간들. 말소리 앞뒤로 숨 쉴 틈(LEAD/GAP/TAIL)을 붙인다."""
    ps = pieces_of(name)
    cuts = []
    for k, (a, b, _) in enumerate(ps):
        pre = LEAD if k == 0 else GAP / 2
        post = TAIL if k == len(ps) - 1 else GAP / 2
        cuts.append([max(0.0, a - pre), b + post])
    # 붙어 있는 문장끼리 겹치면 가운데에서 나눈다 (같은 소리가 두 번 들리지 않게)
    for k in range(1, len(cuts)):
        if cuts[k][0] < cuts[k - 1][1]:
            mid = (cuts[k][0] + cuts[k - 1][1]) / 2
            cuts[k - 1][1] = cuts[k][0] = mid
    return [tuple(c) for c in cuts]


def scene_list():
    plan = json.loads((ROOT / "plan.json").read_text())
    intro = {"num": 0, "name": "intro", "kind": "intro", "dur": 0, "music": "calm", "sfx": []}
    return [intro] + plan["scenes"]


def voice_len(name):
    return sum(b - a for a, b in source_cuts(name))


def target_dur(s):
    v = voice_len(s["name"])
    if s["kind"] == "film":
        return s["dur"]
    if s["kind"] == "clip" and s["name"] != "authority":
        return round(max(CLIP_MIN, v), 2)
    if s["kind"] == "screen":
        return round(max(40.0, v), 2)
    return round(max(3.0, v), 2)


def cmd_plan():
    scenes = scene_list()
    durs = {s["name"]: target_dur(s) for s in scenes if s["name"] != "intro"}
    (ROOT / "assets/face/durs.json").write_text(json.dumps(durs, ensure_ascii=False, indent=1))
    total = sum(durs.values()) + voice_len("intro")
    print(f"총 {total / 60:.1f}분 (첫 인사 {voice_len('intro'):.1f}초 포함)")
    longer = []
    for s in scenes[1:]:
        r = ROOT / "renders_nocap" / f"{Path(s['dir']).name}.mp4"
        have = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(r)],
                                    capture_output=True, text=True).stdout or 0)
        if durs[s["name"]] > have + 0.1:
            longer.append(Path(s["dir"]).name)
    (ROOT / "assets/face/rerender.txt").write_text("\n".join(longer) + "\n")
    print("다시 렌더링할 장면", len(longer), longer)


# ------------------------------------------------------------------ build
def face_box(cuts, w, h, top_bias):
    """원본에서 얼굴을 가운데 두고 자를 사각형 (x, y)."""
    ts = [p for p in track if any(a - 0.5 <= p["t"] <= b + 0.5 for a, b in cuts)] or track
    cx, cy = median(p["cx"] for p in ts), median(p["cy"] for p in ts)
    x = int(min(max(0, cx - w / 2), 1920 - w)) // 2 * 2
    y = int(min(max(0, cy - top_bias), 1080 - h)) // 2 * 2
    return x, y


def face_chain(cuts, first_input):
    """얼굴 원본 구간들을 이어 붙이는 필터 (영상 [fvc], 목소리 [fa]).
    구간마다 입력을 따로 연다 (한 입력을 여러 번 자르면 메모리를 많이 써서 멈춘다)."""
    inputs, parts, labels_v, labels_a = [], [], [], []
    for k, (a, b) in enumerate(cuts):
        i = first_input + k
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(FACE)]
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS[fv{k}]")
        parts.append(f"[{i}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0.0, b - a - 0.03):.3f}:d=0.03[fa{k}]")
        labels_v.append(f"[fv{k}]")
        labels_a.append(f"[fa{k}]")
    n = len(cuts)
    parts.append("".join(labels_v) + f"concat=n={n}:v=1:a=0[fvc]")
    parts.append("".join(labels_a) + f"concat=n={n}:v=0:a=1[fa]")
    return inputs, parts


def compose_scene(s, d, res_dir):
    """장면 하나: 화면 영상(무음) + 목소리 wav + 클립 소리 wav를 out/final_work/에 만든다."""
    name = s["name"]
    key = f"{s['num']:02d}-{name}"
    vout, aout, cout = WORK / f"{key}.mkv", WORK / f"{key}_voice.wav", WORK / f"{key}_clip.wav"
    cuts = source_cuts(name)
    full = s["kind"] in FULL_KINDS or name in FULL_NAMES
    inputs, fc = [], []
    if name != "intro":
        inputs += ["-i", str(res_dir / f"{key}.mp4")]
    if cuts:
        fi = 0 if name == "intro" else 1
        finputs, parts = face_chain(cuts, fi)
        inputs += finputs
        fc += parts
        vlen = sum(b - a for a, b in cuts)
        extra = fi + len(cuts)  # 다음 입력 번호
    else:
        vlen, fi, extra = 0, None, 1
    base = f"color=c=0x05060f:s=1920x1080:r=30:d={d:.3f}"
    if name == "intro":
        # 얼굴 전체 화면 + 「웰컴 투 무협 월드」 썸네일 (강소라 배우 이름이 나올 때부터)
        thumb = ROOT / "assets/images/ref_welcome_wuxia_thumb.png"
        inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", str(thumb)]
        name_at = 4.95 - cuts[0][0]
        fc += ["[fvc]fps=30,scale=1920:1080,setsar=1[bg]",
               f"[{extra}:v]scale=700:-2,pad=iw+12:ih+12:6:6:color=white,format=rgba,"
               f"fade=t=in:st={name_at:.2f}:d=0.3:alpha=1,fade=t=out:st={name_at + 6.5:.2f}:d=0.4:alpha=1[th]",
               "[bg][th]overlay=x=W-w-90:y=110:shortest=1,trim=0:" + f"{d:.3f}" + "[v]"]
    elif s["kind"] in NO_FACE or s["kind"] in VOICE_ONLY or not cuts:
        fc = [p for p in fc if "[fv" not in p and not p.endswith("[fvc]")]  # 얼굴 영상은 쓰지 않음 (목소리는 따로 뽑음)
        inputs = inputs[:2]
        fc += [f"[0:v]fps=30,scale=1920:1080,setsar=1,tpad=stop_mode=clone:stop_duration=30,trim=0:{d:.3f},setpts=PTS-STARTPTS[v]"]
    elif full:
        x, y = face_box(cuts, 1060, 1080, 540)
        fc += [f"{base}[bgc]",
               f"[fvc]fps=30,crop=1060:1080:{x}:{y},setsar=1[face]",
               "[0:v]fps=30,scale=820:-2,setsar=1,pad=iw+8:ih+8:4:4:color=0xb4e61d,tpad=stop_mode=clone:stop_duration=30[card]",
               "[bgc][face]overlay=x=0:y=0:eof_action=repeat[t1]",
               f"[t1][card]overlay=x=1066:y=(H-h)/2:shortest=0,trim=0:{d:.3f},setpts=PTS-STARTPTS[v]"]
    else:
        x, y = face_box(cuts, 720, 810, 330)
        fc += [f"[fvc]fps=30,crop=720:810:{x}:{y},scale=384:432,setsar=1,pad=392:440:4:4:color=0xb4e61d,format=rgba,"
               f"fade=t=out:st={max(0.0, vlen - 0.35):.2f}:d=0.35:alpha=1[pip]",
               f"[0:v]fps=30,scale=1920:1080,setsar=1,tpad=stop_mode=clone:stop_duration=30,trim=0:{d:.3f},setpts=PTS-STARTPTS[main]",
               f"[main][pip]overlay=x=W-w-36:y={36 if s['kind'] in PIP_TOP else 'H-h-36'}:eof_action=pass[v]"]
    vparts = [p for p in fc if ":a]" not in p.split("]")[0] + "]" and not p.endswith("[fa]")]
    graph = ";".join(vparts)
    if not (vout.exists() and aout.exists()):
        run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-t", f"{d:.3f}", "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(vout) + ".part.mkv"])
        Path(str(vout) + ".part.mkv").rename(vout)  # 중간에 실패하면 깨진 파일이 남지 않게
        # 목소리
        if cuts:
            ainputs, aparts = face_chain(cuts, 0)
            agraph = ";".join(p for p in aparts if ":a]" in p.split("]")[0] + "]" or p.endswith("[fa]"))
            agraph += f";[fa]aresample={SR},aformat=channel_layouts=stereo,apad,atrim=0:{d:.3f}[fo]"
            run(["ffmpeg", "-loglevel", "error", "-y", *ainputs, "-filter_complex", agraph, "-map", "[fo]", "-c:a", "pcm_s16le", str(aout)])
        else:
            run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", f"{d:.3f}", "-i", f"anullsrc=r={SR}:cl=stereo", str(aout)])
    # 클립 소리 (렌더에 있으면)
    src = res_dir / f"{key}.mp4"
    has_a = name != "intro" and bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(src)],
                                                    capture_output=True, text=True).stdout.strip())
    if has_a:
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-af", f"aresample={SR},aformat=channel_layouts=stereo,apad,atrim=0:{d:.3f}",
             "-c:a", "pcm_s16le", str(cout)])
    else:
        run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", f"{d:.3f}", "-i", f"anullsrc=r={SR}:cl=stereo", str(cout)])
    return vout, aout, cout


def read_wav(p):
    with wave.open(str(p)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        return x.reshape(-1, w.getnchannels())


def write_wav(p, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def split_caption(text, limit=22):
    """자막을 한 줄(약 22자 이하)씩, 띄어쓰기 기준으로 나눈다."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > limit:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    # 마지막 줄이 너무 짧으면 앞줄과 다시 나눈다
    if len(lines) > 1 and len(lines[-1]) <= 4 and len(lines[-2]) + len(lines[-1]) + 1 <= limit + 6:
        last = lines.pop()
        lines[-1] = lines[-1] + " " + last
    return lines


def ass_time(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_captions(scenes, starts, durs):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Pretendard Caption,50,&H00FFFFFF,&H00FFFFFF,&H380F0605,&H380F0605,0,0,0,0,100,100,0,0,3,16,0,2,60,60,58,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev, srt = [], []
    for s in scenes:
        name = s["name"]
        cuts, ps = source_cuts(name), pieces_of(name)
        if not ps:
            continue
        full = s["kind"] in FULL_KINDS or name in FULL_NAMES or name == "intro"
        mr = 60 if full or s["kind"] in NO_FACE or s["kind"] in VOICE_ONLY or s["kind"] in PIP_TOP else 470
        # 원본 시간 → 장면 안 시간
        offs, acc = [], 0.0
        for a, b in cuts:
            offs.append((a, acc))
            acc += b - a
        for k, (a, b, text) in enumerate(ps):
            ca, off = offs[k]
            t0 = starts[name] + off + (a - ca)
            dur = b - a
            lines = split_caption(text)
            tot = sum(len(x) for x in lines)
            t = t0
            for ln in lines:
                dd = dur * len(ln) / tot
                end = min(t + dd + 0.15, starts[name] + durs[name])
                ev.append(f"Dialogue: 0,{ass_time(t)},{ass_time(end)},Cap,,60,{mr},58,,{ln}")
                srt.append((t, end, ln))
                t += dd
    (WORK / "captions.ass").write_text(head + "\n".join(ev) + "\n")
    out = []
    for i, (a, b, ln) in enumerate(srt, 1):
        f = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}"
        out += [str(i), f"{f(a)} --> {f(b)}", ln, ""]
    (ROOT / "out/captions_final.srt").write_text("\n".join(out))


def music_bed(scenes, durs, voice):
    total = sum(durs[s["name"]] for s in scenes)
    n = int(total * SR)
    bed = np.zeros((n, 2), dtype=np.float32)
    music = {"wuxia": read_wav(ROOT / "assets/audio/bgm_wuxia.wav"), "calm": read_wav(ROOT / "assets/audio/bgm_calm.wav")}
    gain = {"wuxia": 0.20, "calm": 0.17}
    pos, prev, t, fade = {"wuxia": 0, "calm": 0}, None, 0.0, int(0.6 * SR)
    for s in scenes:
        d = durs[s["name"]]
        a, b = int(t * SR), min(n, int((t + d) * SR))
        kind = s["music"] if s["music"] in music else ("wuxia" if s["kind"] == "film" else None)
        if kind and b > a:
            src = music[kind]
            seg = np.take(src, np.arange(pos[kind], pos[kind] + (b - a)) % len(src), axis=0)
            pos[kind] += b - a
            g = gain[kind] * (0.6 if s["kind"] in ("clip", "split", "film") else 1.0)
            env = np.full(b - a, g, dtype=np.float32)
            if prev != kind:
                k = min(fade, b - a)
                env[:k] *= np.linspace(0, 1, k)
            bed[a:b] += seg * env[:, None]
        prev = kind
        t += d
    sfx = {k: read_wav(ROOT / f"assets/audio/sfx_{k}.wav") for k in ("whoosh", "stamp", "ding", "tick", "brush")}
    sg = {"whoosh": 0.35, "stamp": 0.55, "ding": 0.3, "tick": 0.25, "brush": 0.3}
    t = 0.0
    for s in scenes:
        if s["kind"] != "film" and t > 0:
            x = sfx["whoosh"]
            i = int(max(0, t - 0.25) * SR)
            bed[i:i + len(x)] += x[: max(0, n - i)] * 0.12
        for k, off in s["sfx"]:
            if off < durs[s["name"]]:
                x = sfx[k]
                i = int((t + off) * SR)
                bed[i:i + len(x)] += x[: max(0, n - i)] * sg[k]
        t += durs[s["name"]]
    # 목소리가 나오는 동안 음악을 더 낮춘다
    act = np.abs(voice[:n]).mean(axis=1)
    win = int(0.3 * SR)
    act = np.convolve(act, np.ones(win) / win, mode="same")
    duck = 1.0 - 0.55 * np.clip(act / 0.01, 0, 1)
    return bed * duck[:, None], duck


def cmd_build(res):
    WORK.mkdir(parents=True, exist_ok=True)
    scenes = scene_list()
    durs = json.loads((ROOT / "assets/face/durs.json").read_text())
    durs["intro"] = round(voice_len("intro"), 2)
    starts, t = {}, 0.0
    for s in scenes:
        starts[s["name"]] = t
        t += durs[s["name"]]
    total = t
    vl, al, cl = [], [], []
    for s in scenes:
        v, a, c = compose_scene(s, durs[s["name"]], ROOT / "renders_nocap")
        vl.append(v)
        al.append(a)
        cl.append(c)
        print("ok", s["name"], durs[s["name"]], flush=True)
    (WORK / "v.txt").write_text("".join(f"file '{p}'\n" for p in vl))
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "v.txt"), "-c", "copy", str(WORK / "video.mkv")])
    voice = np.concatenate([read_wav(p) for p in al])
    clip = np.concatenate([read_wav(p) for p in cl])
    bed, duck = music_bed(scenes, durs, voice)
    n = min(len(voice), len(clip), len(bed))
    # 목소리: 저음 정리는 ffmpeg에서, 여기서는 섞기만
    (ROOT / "out/stems").mkdir(parents=True, exist_ok=True)
    write_wav(ROOT / "out/stems/voice.wav", voice[:n])
    write_wav(ROOT / "out/stems/music_sfx_final.wav", bed[:n])
    clip_d = clip[:n] * (0.35 + 0.55 * duck[:n, None])
    write_wav(ROOT / "out/stems/clip_audio_final.wav", clip_d)
    build_captions(scenes, starts, durs)
    fontsdir = ROOT / "assets/fonts"
    for r in res:
        h = int(r)
        out = ROOT / f"out/wuxia-showdown-face-{h}p.mp4"
        vf = f"ass={WORK / 'captions.ass'}:fontsdir={fontsdir}" + (f",scale=-2:{h}" if h != 1080 else "")
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(WORK / "video.mkv"), "-i", str(ROOT / "out/stems/voice.wav"),
             "-i", str(ROOT / "out/stems/clip_audio_final.wav"), "-i", str(ROOT / "out/stems/music_sfx_final.wav"),
             "-filter_complex",
             "[1:a]highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2[vo];"
             "[vo][2:a][3:a]amix=inputs=3:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.89:level=false[a]",
             "-map", "0:v", "-map", "[a]", "-vf", vf, "-c:v", "libx264", "-preset", "medium" if h == 1080 else "veryfast",
             "-crf", "19" if h == 1080 else "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
             "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)])
        print("done", out, f"{total / 60:.1f} min")


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        cmd_plan()
    else:
        cmd_build(sys.argv[2:] or ["720"])
