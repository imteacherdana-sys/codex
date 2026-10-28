"""렌더링된 장면을 이어 붙이고 음악·효과음을 섞어 완성본을 만든다.

입력: plan.json (build.py가 만듦), renders/<장면>.mp4, assets/audio/*.wav
출력 (out/):
  wuxia-showdown-final.mp4   완성본 (화면 + 클립 원본 소리 + 배경음악 + 효과음, 내레이션 없음)
  stems/clip_audio.wav       클립 원본 소리만
  stems/music_sfx.wav        배경음악 + 효과음만 (녹음본을 얹을 때 이 둘을 따로 조절)
  captions.srt               대본 자막 (녹음 가이드 겸 업로드용 자막)
  recording-script.md        장면별 타임코드 + 읽을 문장

사용: python3 tools/assemble.py
"""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
SR = 48000


def run(cmd):
    subprocess.run(cmd, check=True)


def read_wav(p):
    with wave.open(str(p)) as w:
        n = w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
        return x.reshape(-1, w.getnchannels())


def write_wav(p, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def tc(t, sep=","):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"


def main():
    plan = json.loads((ROOT / "plan.json").read_text())
    scenes = plan["scenes"]
    (OUT / "norm").mkdir(parents=True, exist_ok=True)
    (OUT / "stems").mkdir(parents=True, exist_ok=True)

    # 1) 장면마다 길이·형식을 맞춘다 (소리가 없는 장면에는 무음 트랙)
    lst = []
    for s in scenes:
        src = ROOT / "renders" / f"{Path(s['dir']).name}.mp4"
        dst = OUT / "norm" / f"{Path(s['dir']).name}.mp4"
        has_audio = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(src)],
                                        capture_output=True, text=True).stdout.strip())
        d = s["dur"]
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", str(src)]
        if not has_audio:
            cmd += ["-f", "lavfi", "-t", str(d), "-i", f"anullsrc=r={SR}:cl=stereo"]
        cmd += ["-filter_complex", f"[0:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=2,trim=0:{d},setpts=PTS-STARTPTS[v];"
                f"[{0 if has_audio else 1}:a]aresample={SR},aformat=channel_layouts=stereo,apad,atrim=0:{d},asetpts=PTS-STARTPTS[a]",
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "pcm_s16le", "-t", str(d), str(dst).replace(".mp4", ".mkv")]
        run(cmd)
        lst.append(f"file '{str(dst).replace('.mp4', '.mkv')}'")
    (OUT / "norm" / "list.txt").write_text("\n".join(lst) + "\n")
    video = OUT / "video_clipaudio.mkv"
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "norm" / "list.txt"), "-c", "copy", str(video)])
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", str(OUT / "stems" / "clip_audio.wav")])

    # 2) 배경음악 + 효과음
    total = sum(s["dur"] for s in scenes)
    n = int(total * SR) + SR
    bed = np.zeros((n, 2), dtype=np.float32)
    music = {"wuxia": read_wav(ROOT / "assets/audio/bgm_wuxia.wav"), "calm": read_wav(ROOT / "assets/audio/bgm_calm.wav")}
    gain = {"wuxia": 0.20, "calm": 0.17}
    duck_kinds = {"clip", "split", "film"}
    t = 0.0
    prev = None
    pos = {"wuxia": 0, "calm": 0}
    fade = int(0.6 * SR)
    for s in scenes:
        a, b = int(t * SR), int((t + s["dur"]) * SR)
        kind = s["music"] if s["music"] in music else ("wuxia" if s["kind"] == "film" else None)
        if kind:
            src = music[kind]
            seg = np.take(src, np.arange(pos[kind], pos[kind] + (b - a)) % len(src), axis=0)
            pos[kind] += b - a
            g = gain[kind] * (0.6 if s["kind"] in duck_kinds else 1.0)
            env = np.full(b - a, g, dtype=np.float32)
            if prev != kind:
                k = min(fade, b - a)
                env[:k] *= np.linspace(0, 1, k)
            bed[a:b] += seg * env[:, None]
        prev = kind
        t += s["dur"]
    sfx = {name: read_wav(ROOT / f"assets/audio/sfx_{name}.wav") for name in ("whoosh", "stamp", "ding", "tick", "brush")}
    sfx_gain = {"whoosh": 0.35, "stamp": 0.55, "ding": 0.3, "tick": 0.25, "brush": 0.3}
    t = 0.0
    for s in scenes:
        # 장면이 바뀔 때마다 가벼운 휙 (영상 클립 장면 제외)
        if s["kind"] not in ("film",) and t > 0:
            x = sfx["whoosh"]
            i = int(max(0, t - 0.25) * SR)
            bed[i:i + len(x)] += x[: len(bed) - i] * 0.12
        for name, off in s["sfx"]:
            x = sfx[name]
            i = int((t + off) * SR)
            bed[i:i + len(x)] += x[: len(bed) - i] * sfx_gain[name]
        t += s["dur"]
    bed = bed[: int(total * SR)]
    write_wav(OUT / "stems" / "music_sfx.wav", bed)

    # 3) 완성본: 클립 소리 + 배경음악·효과음, 마지막에 라우드니스 맞춤
    final = OUT / "wuxia-showdown-final.mp4"
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-i", str(OUT / "stems" / "music_sfx.wav"),
         "-filter_complex", "[0:a]volume=0.9[c];[c][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.89:level=false[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", str(final)])

    # 4) 자막과 녹음 대본
    srt, md = [], ["# 무협 쇼다운 녹음 대본", "", "완성본의 자막과 같은 문장이에요. 타임코드에 맞춰 읽고, 녹음본을 `stems/music_sfx.wav`·`stems/clip_audio.wav`와 함께 얹으면 돼요.", ""]
    k = 0
    for s in scenes:
        md.append(f"## {s['num']:02d}. {s['name']}  ({tc(s['start'], '.')[:-4]} – {tc(s['start'] + s['dur'], '.')[:-4]})")
        if not s["caps"]:
            md.append("(멘트 없음)")
        for c in s["caps"]:
            k += 1
            srt += [str(k), f"{tc(c['start'])} --> {tc(c['start'] + c['dur'])}", c["text"], ""]
            md.append(f"- `{tc(c['start'], '.')[:-4]}` {c['text']}")
        md.append("")
    (OUT / "captions.srt").write_text("\n".join(srt))
    (OUT / "recording-script.md").write_text("\n".join(md))
    print("done", final, f"{total / 60:.1f} min")


if __name__ == "__main__":
    main()
