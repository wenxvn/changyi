"""解析4个医院数据并归一化"""
import json, csv, re, os

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

def clean_kw(t):
    return [k.strip() for k in re.split(r'[，,；;、\s]+', t) if k.strip() and len(k.strip()) > 1 and k.strip() not in '的及等与和：（）()']

def save(hid, name, level, docs):
    out = {"hospital": name, "hospital_id": hid, "hospital_level": level, "last_updated": "2026-06-03", "total_doctors": len(docs), "doctors": docs}
    with open(os.path.join(OUT_DIR, f"doctors_h{hid}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[{name}] {len(docs)}位 → doctors_h{hid}.json")

# ====== 二院 JSON数组 ======
def parse_2nd():
    with open("D:/常州市第二人民医院.json", "r", encoding="utf-8") as f:
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
def parse_maternity():
    with open("D:/常州市妇幼保健院.csv", "r", encoding="utf-8") as f:
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
def parse_children():
    with open("D:/常州市儿童医院医生资料.txt", "r", encoding="utf-8") as f:
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
def parse_tcm():
    with open("D:/常州市中医医院.md", "r", encoding="utf-8") as f:
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

if __name__ == "__main__":
    print("=" * 50)
    save(2, "常州市第二人民医院", "三级甲等", parse_2nd())
    save(7, "常州市妇幼保健院", "三级甲等", parse_maternity())
    save(6, "常州市儿童医院", "三级甲等", parse_children())
    save(3, "常州市中医医院", "三级甲等", parse_tcm())
    # 一院数据直接用原有 JSON
    with open(os.path.join(os.path.dirname(__file__), "doctors.json"), "r", encoding="utf-8") as f:
        d = json.load(f)
    d["hospital_id"] = 1; d["hospital"] = "常州市第一人民医院"
    with open(os.path.join(OUT_DIR, "doctors_h1.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"[常州市第一人民医院] 123位 → doctors_h1.json")
    print("=" * 50 + "\nDone!")
