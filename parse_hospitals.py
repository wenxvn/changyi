"""Parse supplied hospital source files into deterministic doctor datasets.

The old version depended on four absolute Windows paths and always rewrote
the repository data directory.  This CLI keeps the same normalizers while
making input and output explicit, so a source can be reviewed before it is
activated in a Region Pack.
"""

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent

def clean_kw(t):
    return [k.strip() for k in re.split(r'[，,；;、\s]+', t) if k.strip() and len(k.strip()) > 1 and k.strip() not in '的及等与和：（）()']

def save(hid, name, level, docs, out_dir, *, region_code, last_updated):
    out = {
        "hospital": name,
        "hospital_id": hid,
        "hospital_level": level,
        "region_code": region_code,
        "last_updated": last_updated,
        "total_doctors": len(docs),
        "doctors": docs,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / f"doctors_h{hid}.json").open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[{name}] {len(docs)}位 → doctors_h{hid}.json")

# ====== 二院 JSON数组 ======
def parse_2nd(input_path):
    with Path(input_path).open("r", encoding="utf-8") as f:
        raw = json.load(f)
    docs = []
    for x in raw:
        n = (x.get("name") or "").strip()
        if not n: continue
        dept = (x.get("department") or "").strip()
        title = (x.get("title") or "").strip()
        spec = (x.get("specialty") or "").strip()
        acad = (x.get("academic") or "").strip()
        at = ""; tc = title
        for t in ["教授","副教授","讲师"]:
            if t in title: at = t; break
        if "硕导" in title or "硕士生导师" in title: at = at + ("、硕导" if at else "硕导")
        if "博导" in title or "博士生导师" in title: at = at + ("、博导" if at else "博导")
        ach = [p.strip() for p in re.split(r'[，,；;、]', acad) if p.strip() and len(p.strip()) > 2]
        nf = "国自然" in acad or "国家自然科学基金" in acad
        pm = re.search(r'专利\s*(\d+)', acad); pat = int(pm.group(1)) if pm else None
        sm = re.search(r'SCI\s*论文\s*(\d+)|SCI\s*(\d+)', acad); sci = int(sm.group(1) or sm.group(2)) if sm else None
        docs.append({"name": n, "department": dept, "title": tc, "academic_title": at,
            "keywords": clean_kw(spec)[:15], "specialty": spec, "achievements": ach[:5],
            "national_funding": nf, "patents": pat, "sci_papers": sci, "position": acad if any(p in acad for p in ["主任","科长","书记","院长","所长"]) else ""})
    return docs

# ====== 妇幼 CSV ======
def parse_maternity(input_path):
    with Path(input_path).open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    docs, seen = [], set()
    for r in rows:
        n = (r.get("医生姓名") or "").strip()
        if not n or n in seen: continue
        seen.add(n)
        dept = (r.get("科室") or "").strip()
        title = (r.get("职称/职位（公开页）") or "").split("；")[0].strip()
        spec = (r.get("擅长/诊疗领域（公开页摘要）") or "").strip()
        acad = (r.get("论文/学术作品/科研项目（公开页摘要）") or "").strip()
        rat = (r.get("患者/评价/平台指标（非医疗质量）") or "").strip()
        rm = re.search(r'推荐度\s*(\d+\.?\d*)', rat); pr = float(rm.group(1)) if rm else None
        sm = re.search(r'SCI.*?(\d+)\s*篇', acad); sci = int(sm.group(1)) if sm else None
        nf = "国自然" in acad or "国家自然科学基金" in acad
        docs.append({"name": n, "department": dept, "title": title, "academic_title": "",
            "keywords": clean_kw(spec)[:15], "specialty": spec, "patient_rating": pr,
            "national_funding": nf, "sci_papers": sci, "achievements": [p.strip() for p in re.split(r'[；;]', acad) if p.strip() and len(p.strip()) > 3][:5]})
    return docs

# ====== 儿童医院 TXT ======
def parse_children(input_path):
    with Path(input_path).open("r", encoding="utf-8") as f:
        text = f.read()
    docs = []
    for m in re.finditer(r'\d+\.\s*姓名：(.+?)\n\s*职称：(.+?)(?:\n\s*接诊量：.*?)?\n\s*擅长领域：(.+?)(?=\n\s*(?:学术成就|出诊时间|$))', text, re.DOTALL):
        name, title, spec = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        pos = m.start()
        before = text[:pos]
        dm = list(re.finditer(r'={30,}\s*\n\s*[一二三四五六七八九十]+、(.+?)\s*\n={30,}', before))
        dept = dm[-1].group(1).strip() if dm else "儿科"
        end = pos + 5000; nm = re.search(r'\n\s*\d+\.\s*姓名：', text[pos:])
        if nm: end = min(end, pos + nm.start())
        seg = text[pos:end]
        am = re.findall(r'学术成就：\s*\n((?:\s*-.+\n)+)', seg)
        acad = re.sub(r'^\s*[-•]\s*', '', am[0], flags=re.MULTILINE) if am else ""
        ach = [l.strip() for l in acad.split('\n') if l.strip() and len(l.strip()) > 3]
        at = ""
        for t in ["教授","副教授","讲师"]:
            if t in title: at = t; break
        if "硕导" in title: at = at + ("、硕导" if at else "硕导")
        sm = re.search(r'SCI\s*(\d+)', acad); sci = int(sm.group(1)) if sm else None
        nf = "国自然" in acad
        docs.append({"name": name, "department": dept, "title": title, "academic_title": at,
            "keywords": clean_kw(spec)[:15], "specialty": spec, "achievements": ach[:5],
            "sci_papers": sci, "national_funding": nf})
    return docs

# ====== 中医医院 MD ======
def parse_tcm(input_path):
    with Path(input_path).open("r", encoding="utf-8") as f:
        text = f.read()
    docs = []
    for sec in re.split(r'\n### ', text)[1:]:
        lines = sec.strip().split('\n')
        hdr = lines[0].strip()
        if hdr.startswith("其他") or hdr.startswith("代表") or hdr.startswith("手术"): continue
        hm = re.match(r'(.+?)\s*[—\-]\s*(.+)', hdr)
        if not hm: continue
        name = hm.group(1).strip()
        title_raw = hm.group(2).strip()
        tc = re.sub(r'[（(].*?[）)]', '', title_raw).strip()
        pm = re.search(r'[（(](.*?)[）)]', title_raw); pos = pm.group(1) if pm else ""
        full = "\n".join(lines[1:])
        td = {}
        for l in lines[1:]:
            rm = re.match(r'\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', l)
            if rm: td[rm.group(1).strip()] = rm.group(2).strip()
        dept = td.get("科室", "")
        spec = td.get("擅长领域", "")
        acad = td.get("学术成就", "") + " " + td.get("论文", "") + " " + td.get("获奖", "") + " " + td.get("荣誉", "") + " " + td.get("课题", "")
        at = ""
        for t in ["教授","副教授","讲师"]:
            if t in title_raw: at = t; break
        if "硕导" in title_raw: at = at + ("、硕导" if at else "硕导")
        if "博导" in title_raw: at = at + ("、博导" if at else "博导")
        if "博士" in title_raw: at = at + ("、博士" if at else "博士")
        sm = re.search(r'SCI\s*(?:论文)?\s*(\d+)\s*篇', full); sci = int(sm.group(1)) if sm else None
        pm2 = re.search(r'论文.*?(\d+)\s*篇', full); tp = int(pm2.group(1)) if pm2 else None
        nf = "国自然" in full or "国家自然科学基金" in full or "973" in full
        pm3 = re.search(r'专利\s*(\d+)', full); pat = int(pm3.group(1)) if pm3 else None
        awards = [m.group(1).strip() for m in re.finditer(r'([^，,；;|\n]+?奖[项]?)', full) if len(m.group(1).strip()) > 2]
        honors = [h.strip() for h in re.split(r'[，,；;、]', td.get("荣誉","")) if h.strip() and len(h.strip()) > 2]
        docs.append({"name": name, "department": dept, "title": tc, "academic_title": at,
            "keywords": clean_kw(spec)[:15], "specialty": spec, "position": pos,
            "sci_papers": sci, "total_papers": tp, "national_funding": nf, "patents": pat,
            "awards": awards[:5], "honors": honors[:5],
            "achievements": [p.strip() for p in acad.split("；") if p.strip() and len(p.strip()) > 3][:5]})
    return docs

def _source_path(explicit: Path | None, input_dir: Path | None, file_name: str) -> Path | None:
    if explicit:
        return explicit
    return input_dir / file_name if input_dir else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, help="包含公开源文件的目录")
    parser.add_argument("--second", type=Path, help="二院 JSON 源文件")
    parser.add_argument("--maternity", type=Path, help="妇幼 CSV 源文件")
    parser.add_argument("--children", type=Path, help="儿童医院 TXT 源文件")
    parser.add_argument("--tcm", type=Path, help="中医医院 Markdown 源文件")
    parser.add_argument("--first-doctors", type=Path, help="一院现有 doctors.json 源文件")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--region", default="320400", help="输出数据所属 Region Pack 编码")
    parser.add_argument("--last-updated", default="2026-06-03")
    args = parser.parse_args(argv)
    input_dir = args.input_dir.resolve() if args.input_dir else None
    output_dir = args.output_dir.resolve()
    sources = {
        "second": _source_path(args.second, input_dir, "常州市第二人民医院.json"),
        "maternity": _source_path(args.maternity, input_dir, "常州市妇幼保健院.csv"),
        "children": _source_path(args.children, input_dir, "常州市儿童医院医生资料.txt"),
        "tcm": _source_path(args.tcm, input_dir, "常州市中医医院.md"),
        "first": _source_path(args.first_doctors, input_dir, "doctors.json"),
    }
    if not any(sources.values()):
        parser.error("至少提供 --input-dir 或一个医院源文件参数")
    for key, path in sources.items():
        if path and not path.is_file():
            parser.error(f"源文件不存在: {path}")

    print("=" * 50)
    if sources["second"]:
        save(2, "常州市第二人民医院", "三级甲等", parse_2nd(sources["second"]), output_dir, region_code=args.region, last_updated=args.last_updated)
    if sources["maternity"]:
        save(7, "常州市妇幼保健院", "三级甲等", parse_maternity(sources["maternity"]), output_dir, region_code=args.region, last_updated=args.last_updated)
    if sources["children"]:
        save(6, "常州市儿童医院", "三级甲等", parse_children(sources["children"]), output_dir, region_code=args.region, last_updated=args.last_updated)
    if sources["tcm"]:
        save(3, "常州市中医医院", "三级甲等", parse_tcm(sources["tcm"]), output_dir, region_code=args.region, last_updated=args.last_updated)
    if sources["first"]:
        d = json.loads(sources["first"].read_text(encoding="utf-8"))
        d["hospital_id"] = 1
        d["hospital"] = "常州市第一人民医院"
        d["region_code"] = args.region
        (output_dir / "doctors_h1.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[常州市第一人民医院] {len(d.get('doctors', []))}位 → doctors_h1.json")
    print("=" * 50 + "\nDone!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
