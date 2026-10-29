"""완성본 편집점을 프리미어로 넘긴다: face_all.mp4를 final 영상 시간표에 맞춰 컷 편집한 시퀀스.

출력 (upload/premiere/):
  wuxia_face_cuts.xml   프리미어 '가져오기'용 (Final Cut Pro 7 XML)
                        V1 = 완성본 영상, V2·A2 = face_all.mp4 컷 (편집점을 끌어 늘리면 잘린 말을 되살릴 수 있음)
  wuxia_face_cuts.edl   같은 내용의 EDL (CMX3600, face_all.mp4 컷만)
  wuxia_face_cuts.csv   컷 목록: 완성본 시간 · 원본 시간 · 그 구간에서 한 말
사용: python3 tools/export_premiere.py [완성본 파일 이름] [얼굴 파일 이름]
"""
import csv
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_edit as F  # noqa: E402

ROOT = F.ROOT
FPS = 30
FINAL_NAME = sys.argv[1] if len(sys.argv) > 1 else "wuxia-showdown-final-1080p.mp4"
FACE_NAME = sys.argv[2] if len(sys.argv) > 2 else "face_all.mp4"
FACE_FRAMES = 27367  # face_all.mp4 912.23초 × 30
OUT = ROOT / "upload/premiere"


def fr(t):
    return int(round(t * FPS))


def tc(frames):
    h, r = divmod(frames, FPS * 3600)
    m, r = divmod(r, FPS * 60)
    s, f = divmod(r, FPS)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def timeline():
    durs = json.loads((ROOT / "assets/face/durs.json").read_text())
    durs["intro"], durs["highlight"] = F.voice_len("intro"), F.HIGHLIGHT_DUR
    cuts, t = [], 0.0
    for s in F.scene_list():
        name = s["name"]
        pos = t
        for (a, b), (_, _, text, _) in zip(F.source_cuts(name), F.pieces_of(name)):
            cuts.append({"scene": name, "rec_in": pos, "rec_out": pos + (b - a), "src_in": a, "src_out": b, "text": text})
            pos += b - a
        t += durs[name]
    return cuts, t


def file_el(fid, name, frames, w=1920, h=1080, audio=True, first=True):
    if not first:
        return f'<file id="{fid}"/>'
    a = ('<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics>'
         '<channelcount>2</channelcount></audio>') if audio else ""
    return (f'<file id="{fid}"><name>{escape(name)}</name><pathurl>{escape(name)}</pathurl>'
            f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><duration>{frames}</duration>'
            f'<media><video><samplecharacteristics><width>{w}</width><height>{h}</height></samplecharacteristics></video>{a}</media></file>')


def clip(cid, name, fid, frames, start, end, src_in, src_out, kind, first, track_link=None):
    rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"
    link = ""
    if track_link:
        link = "".join(f"<link><linkclipref>{ref}</linkclipref><mediatype>{mt}</mediatype><trackindex>{ti}</trackindex><clipindex>{ci}</clipindex></link>"
                       for ref, mt, ti, ci in track_link)
    src = '<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>' if kind == "audio" else ""
    return (f'<clipitem id="{cid}"><name>{escape(name)}</name><enabled>TRUE</enabled><duration>{frames}</duration>{rate}'
            f'<start>{start}</start><end>{end}</end><in>{src_in}</in><out>{src_out}</out>'
            f'{file_el(fid, name, frames, first=first)}{src}{link}</clipitem>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cuts, total = timeline()
    total_f = fr(total)
    # 프레임 경계에서 겹치거나 빈틈이 생기지 않게 정수 프레임으로 맞춘다
    rows = []
    for c in cuts:
        rs, re_ = fr(c["rec_in"]), fr(c["rec_out"])
        si = fr(c["src_in"])
        rows.append({**c, "rs": rs, "re": re_, "si": si, "so": si + (re_ - rs)})
    for a, b in zip(rows, rows[1:]):
        if b["rs"] < a["re"]:
            a["re"] = b["rs"]
            a["so"] = a["si"] + (a["re"] - a["rs"])

    v1 = clip("final-v", FINAL_NAME, "file-final", total_f, 0, total_f, 0, total_f, "video", True,
              [("final-v", "video", 1, 1), ("final-a", "audio", 1, 1)])
    a1 = clip("final-a", FINAL_NAME, "file-final", total_f, 0, total_f, 0, total_f, "audio", False,
              [("final-v", "video", 1, 1), ("final-a", "audio", 1, 1)])
    v2, a2 = [], []
    for k, r in enumerate(rows, 1):
        links = [(f"face-v{k}", "video", 2, k), (f"face-a{k}", "audio", 2, k)]
        v2.append(clip(f"face-v{k}", FACE_NAME, "file-face", FACE_FRAMES, r["rs"], r["re"], r["si"], r["so"], "video", k == 1, links))
        a2.append(clip(f"face-a{k}", FACE_NAME, "file-face", FACE_FRAMES, r["rs"], r["re"], r["si"], r["so"], "audio", False, links))
    fmt = (f'<format><samplecharacteristics><rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>'
           '<width>1920</width><height>1080</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq-1">'
           f'<name>무협쇼다운_face_cuts</name><duration>{total_f}</duration><rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>'
           '<timecode><rate><timebase>30</timebase><ntsc>FALSE</ntsc></rate><string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>'
           f'<media><video>{fmt}<track>{v1}</track><track>{"".join(v2)}</track></video>'
           f'<audio><numOutputChannels>2</numOutputChannels><track>{a1}</track><track>{"".join(a2)}</track></audio></media>'
           '</sequence></xmeml>\n')
    (OUT / "wuxia_face_cuts.xml").write_text(xml)

    edl = ["TITLE: WUXIA_FACE_CUTS", "FCM: NON-DROP FRAME", ""]
    for k, r in enumerate(rows, 1):
        edl.append(f"{k:03d}  FACE_ALL AA/V  C        {tc(r['si'])} {tc(r['so'])} {tc(r['rs'])} {tc(r['re'])}")
        edl.append(f"* FROM CLIP NAME: {FACE_NAME}")
        edl.append(f"* {r['scene']} · {r['text'][:60]}")
        edl.append("")
    (OUT / "wuxia_face_cuts.edl").write_text("\n".join(edl))

    with open(OUT / "wuxia_face_cuts.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["번호", "장면", "완성본 시작", "완성본 끝", "원본 시작", "원본 끝", "한 말"])
        for k, r in enumerate(rows, 1):
            w.writerow([k, r["scene"], tc(r["rs"]), tc(r["re"]), tc(r["si"]), tc(r["so"]), r["text"]])
    print(f"cuts {len(rows)}, total {tc(total_f)} → {OUT}")


if __name__ == "__main__":
    main()
