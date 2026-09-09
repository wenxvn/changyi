"""
常州市智能医疗推荐系统 - 演示版
Smart Medical Recommendation System for Changzhou City
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import math
import json
import os
import sys
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_FEEDBACK_PATH = os.path.join(BASE_DIR, "data", "test_feedback.jsonl")
SYMPTOM_DISEASE_MODEL_DIR = os.path.join(BASE_DIR, "data", "symptom_disease_model")
SYMPTOM_DISEASE_MODEL_PATH = os.path.join(
    SYMPTOM_DISEASE_MODEL_DIR,
    "models",
    "symptom_disease_41_nb.json",
)
_SYMPTOM_DISEASE_RUNTIME = None
_SYMPTOM_DISEASE_RUNTIME_ERROR = None


def _load_symptom_disease_runtime():
    """Lazy-load the local symptom-to-disease model packaged inside this system."""
    global _SYMPTOM_DISEASE_RUNTIME, _SYMPTOM_DISEASE_RUNTIME_ERROR
    if _SYMPTOM_DISEASE_RUNTIME is not None:
        return _SYMPTOM_DISEASE_RUNTIME
    if _SYMPTOM_DISEASE_RUNTIME_ERROR is not None:
        return None

    try:
        if not os.path.exists(SYMPTOM_DISEASE_MODEL_PATH):
            raise FileNotFoundError(SYMPTOM_DISEASE_MODEL_PATH)
        if SYMPTOM_DISEASE_MODEL_DIR not in sys.path:
            sys.path.insert(0, SYMPTOM_DISEASE_MODEL_DIR)

        from inference import load_symptom_alias_map, load_symptom_name_map, predict_with_details
        from labels import load_disease_name_map

        with open(SYMPTOM_DISEASE_MODEL_PATH, "r", encoding="utf-8") as f:
            model = json.load(f)

        _SYMPTOM_DISEASE_RUNTIME = {
            "model": model,
            "disease_name_map": load_disease_name_map(),
            "symptom_alias_map": load_symptom_alias_map(),
            "symptom_name_map": load_symptom_name_map(),
            "predict_with_details": predict_with_details,
        }
        return _SYMPTOM_DISEASE_RUNTIME
    except Exception as exc:
        _SYMPTOM_DISEASE_RUNTIME_ERROR = str(exc)
        return None


def predict_disease_name(condition, details=False):
    """Return the model disease prediction for free-text Chinese symptoms."""
    condition, colloquial_replacements = normalize_patient_expression(condition)
    runtime = _load_symptom_disease_runtime()
    if not runtime:
        result = {
            "disease": "",
            "available": False,
            "error": _SYMPTOM_DISEASE_RUNTIME_ERROR or "model_unavailable",
        }
        return result if details else {"disease": ""}

    result = runtime["predict_with_details"](
        runtime["model"],
        condition,
        disease_name_map=runtime["disease_name_map"],
        symptom_alias_map=runtime["symptom_alias_map"],
        symptom_name_map=runtime["symptom_name_map"],
        top_k=5 if details else 3,
    )
    result["available"] = True
    if details:
        result["colloquial_replacements"] = colloquial_replacements
    return result if details else {"disease": result.get("disease", "")}


def _model_standard_symptom_tags(condition):
    """Convert patient wording into model-backed standard symptom tags."""
    normalized_condition, _ = normalize_patient_expression(condition)
    details = predict_disease_name(normalized_condition, details=True)
    if not details.get("available") or not details.get("normalized_symptoms"):
        return [], details

    known_labels = details.get("known_symptoms", [])
    normalized_codes = details.get("normalized_symptoms", [])
    aliases = details.get("aliases", {})
    tags = []
    seen = set()

    for index, code in enumerate(normalized_codes):
        if code in seen:
            continue
        seen.add(code)
        label = known_labels[index] if index < len(known_labels) else code
        matched_terms = [raw for raw, mapped in aliases.items() if mapped == code]
        tags.append({
            "tag": label,
            "standard_code": code,
            "matched_terms": matched_terms[:5] or [label],
            "body_system": _infer_model_symptom_system(code, label),
            "red_flag_related": _is_model_symptom_red_flag(code, label),
            "source": "symptom_disease_model",
        })
    return tags, details


def _infer_model_symptom_system(code, label):
    text = f"{code} {label}"
    if any(k in text for k in ("cough", "sneezing", "phlegm", "throat", "nose", "breath", "chest", "咳", "喷嚏", "鼻", "喉", "痰", "呼吸", "胸")):
        return "呼吸系统"
    if any(k in text for k in ("abdominal", "diarrhoea", "vomiting", "nausea", "stomach", "appetite", "便", "腹", "胃", "吐", "恶心", "食欲")):
        return "消化系统"
    if any(k in text for k in ("head", "dizziness", "spinning", "balance", "sensorium", "头", "眩晕", "意识", "平衡")):
        return "神经系统"
    if any(k in text for k in ("joint", "muscle", "back", "neck", "关节", "肌肉", "背", "颈")):
        return "运动系统"
    if any(k in text for k in ("skin", "itching", "rash", "yellow", "皮肤", "瘙痒", "皮疹", "黄")):
        return "皮肤系统"
    if any(k in text for k in ("urination", "urine", "尿")):
        return "泌尿系统"
    if any(k in text for k in ("fever", "fatigue", "chills", "malaise", "高烧", "低烧", "乏力", "寒战", "全身")):
        return "感染/全身症状"
    return "未细分症状"


def _is_model_symptom_red_flag(code, label):
    text = f"{code} {label}"
    red_terms = ("chest_pain", "breathlessness", "altered_sensorium", "high_fever", "胸痛", "呼吸困难", "意识", "高烧")
    return any(term in text for term in red_terms)


COLLOQUIAL_SYMPTOM_ALIASES = {
    "喘不上来": "呼吸困难",
    "上不来气": "呼吸困难",
    "透不过气": "呼吸困难",
    "胸口堵": "胸闷",
    "胸口压着": "胸闷",
    "心口疼": "胸痛",
    "心脏疼": "胸痛",
    "嗓子不舒服": "咽痛",
    "喉咙疼": "咽痛",
    "拉肚子": "腹泻",
    "肚子疼": "腹痛",
    "胃不舒服": "胃痛",
    "想吐": "恶心",
    "头昏": "头晕",
    "天旋地转": "眩晕",
    "半边身子没劲": "一侧无力",
    "嘴歪": "口角歪斜",
    "说不清话": "说话不清",
    "身上起疙瘩": "皮疹",
    "皮肤痒": "皮肤瘙痒",
    "眼睛看不清": "视力下降",
    "小便疼": "尿痛",
    "尿里有血": "血尿",
    "血糖高": "糖尿病",
}

KNOWN_DISEASE_PATTERNS = [
    "已确诊", "确诊", "医生说", "诊断为", "检查说", "查出来", "复诊", "术后复查",
    "患有", "得了", "我是", "病史", "既往", "报告提示", "考虑",
]


def normalize_patient_expression(condition):
    text = condition or ""
    normalized = text
    replacements = []
    for raw, standard in COLLOQUIAL_SYMPTOM_ALIASES.items():
        if raw in text and standard not in normalized:
            normalized += f" {standard}"
            replacements.append({"raw": raw, "standard": standard})
    return normalized, replacements


def detect_known_disease(condition):
    text = condition or ""
    has_known_context = any(token in text for token in KNOWN_DISEASE_PATTERNS)
    matches = []
    symptom_like_terms = {
        "胸痛", "胸闷", "心慌", "心悸", "头痛", "头晕", "腰痛", "腰疼", "背痛",
        "腹痛", "腹泻", "恶心", "呕吐", "咳嗽", "发热", "感冒", "鼻塞", "皮肤",
        "皮疹", "过敏", "视力", "眼睛", "牙齿", "牙痛", "听力", "耳鸣", "月经",
        "儿童", "小儿", "怀孕", "孕期",
        "嗓子疼", "咽痛", "喉咙痛", "眩晕", "头昏", "站不稳", "走路不稳", "无法站立", "天旋地转",
        "右下腹痛", "右下腹部痛", "右下部腹痛", "右下腹", "右下部",
    }
    for disease, dept in DISEASE_DEPT_MAP.items():
        if len(disease) < 2:
            continue
        if disease in text and (has_known_context or disease not in symptom_like_terms):
            matches.append((len(disease), disease, dept))
    for rule in DISEASE_DIRECT_RULES:
        if rule["name"] in text:
            matches.append((len(rule["name"]), rule["name"], rule["dept"]))
        elif has_known_context:
            for alias in rule["aliases"]:
                if alias in text and alias not in symptom_like_terms:
                    matches.append((len(alias), rule["name"], rule["dept"]))
    if not matches:
        return {"has_known_disease": False, "disease": "", "department": "", "confidence": 0.0, "source": ""}
    matches.sort(reverse=True)
    _, disease, dept = matches[0]
    return {
        "has_known_disease": bool(has_known_context or disease in text),
        "disease": disease,
        "department": dept,
        "confidence": 0.92 if has_known_context else 0.74,
        "source": "user_stated" if has_known_context else "disease_keyword",
    }


def _candidate_names(disease_candidates):
    return [item.get("name", "") for item in disease_candidates if item.get("name")]


def build_candidate_comparison(disease_candidates):
    names = _candidate_names(disease_candidates)[:3]
    if len(names) < 2:
        return {"need_compare": False, "focus": [], "distinguish_questions": []}

    text = " ".join(names)
    questions = []
    if any(k in text for k in ("心绞痛", "冠脉", "心肌梗死")) and any(k in text for k in ("哮喘", "肺炎", "支气管")):
        questions.append({"id": "chest_breath_detail", "question": "胸闷胸痛是否和活动有关？是否伴大汗、左肩/背部放射痛或明显喘不上气？", "options": ["活动后加重/伴大汗", "主要咳嗽喘息", "都不明显"]})
    if any(k in text for k in ("感冒", "上呼吸道")) and any(k in text for k in ("肺炎", "支气管")):
        questions.append({"id": "resp_infection_detail", "question": "是否有高热、黄痰、胸痛或气短？这些能帮助区分普通感冒和下呼吸道感染。", "options": ["有高热/黄痰/气短", "只有鼻塞咽痛轻咳", "不确定"]})
    if any(k in text for k in ("胃肠炎", "腹")):
        questions.append({"id": "digest_detail", "question": "腹痛是否剧烈或固定在某一位置？是否伴持续呕吐、便血、黑便或发热？", "options": ["有明显危险信号", "轻中度腹泻/呕吐", "不确定"]})
    if any(k in text for k in ("脑卒中", "神经", "头痛")):
        questions.append({"id": "neuro_detail", "question": "是否突然出现一侧无力、口角歪斜、说话不清或剧烈头痛？", "options": ["有突发神经症状", "只是头晕头痛", "不确定"]})
    if any(k in text for k in ("肿瘤", "结节", "癌")):
        questions.append({"id": "tumor_detail", "question": "是否已有影像/病理报告？结节或肿瘤位于哪个部位，是否已做手术/放化疗？", "options": ["已有报告/确诊", "只是体检发现", "不确定"]})

    if not questions:
        questions.append({"id": "topk_detail", "question": "这几个候选方向还需要区分，请补充最困扰您的主要症状、持续时间和是否有检查结果。", "options": []})
    return {"need_compare": True, "focus": names, "distinguish_questions": questions}


def build_followup_questions(condition, analysis, triage=None):
    text = condition or ""
    symptom_tags = analysis.get("symptom_tags", [])
    disease_candidates = analysis.get("disease_candidates", [])
    known_disease = analysis.get("known_disease", {})
    questions = []
    missing = []

    def add(qid, question, options=None, reason=""):
        if any(q["id"] == qid for q in questions):
            return
        questions.append({"id": qid, "question": question, "options": options or [], "reason": reason})

    if known_disease.get("has_known_disease"):
        add("known_disease_status", f"您提到可能是“{known_disease.get('disease')}”，这是已确诊、复诊，还是自己判断？", ["已确诊/复诊", "报告提示但未确诊", "自己怀疑"], "用户已提供疾病名，需要确认置信来源")
        add("known_disease_evidence", "有没有检查报告、影像结果、病理结果或正在用药的信息？", ["有检查/报告", "有用药或治疗史", "暂时没有"], "已知疾病场景优先补充证据和治疗阶段")
        add("known_disease_goal", "这次主要想解决什么问题？", ["复诊开药", "看检查报告", "进一步治疗", "确认挂哪个科"], "明确已知疾病场景下的就诊目的")
    else:
        sparse_symptoms = len(symptom_tags) < 3 or len(text.strip()) < 24
        if len(symptom_tags) < 2 and len(text) < 18:
            missing.append("主要症状信息不足")
            add("main_symptom_more", "请再补充 1-2 个主要症状，例如发热、咳嗽、疼痛部位、胸闷、腹泻等。", [], "症状词不足")
        if not any(k in text for k in ("天", "周", "月", "年", "小时", "昨天", "今天", "刚刚", "持续")):
            missing.append("缺少持续时间")
            add("duration", "这个症状大概持续多久了？", ["1天内", "1周以内", "1-4周", "1个月以上"], "持续时间影响病情分层")
        if not any(k in text for k in ("轻微", "中等", "明显", "非常严重", "严重", "剧烈", "难忍", "加重", "影响", "不影响", "无法", "不能")):
            missing.append("缺少严重程度")
            add("severity", "目前严重程度如何？是否影响日常生活或睡眠？", ["轻微", "中等", "明显影响", "非常严重"], "严重程度影响急症/重症判断")
        mental_context = any(k in text for k in ("难受", "头晕", "头昏", "失眠", "睡不着", "心慌", "焦虑", "压力", "害怕", "紧张"))
        if mental_context:
            add("mental_sleep_stress", "最近是否伴随焦虑紧张、心慌、睡眠差、情绪低落或压力明显？", ["有明显压力/睡眠差", "主要是身体不适", "不确定"], "模糊不适合并头晕/睡眠问题时补充心理睡眠因素")
        if sparse_symptoms:
            add("onset_pattern", "症状是突然出现、逐渐加重，还是反复发作？", ["突然出现", "逐渐加重", "反复发作", "不确定"], "补充发病方式")
            add("symptom_location", "主要不舒服的位置在哪里？例如头部、胸口、腹部、腰背、四肢或皮肤。", [], "补充症状部位")
            add("companion_symptoms", "还伴随哪些表现？", ["发热/咳嗽", "疼痛/胸闷", "腹泻/呕吐", "头晕/乏力", "其他或没有"], "补充伴随症状")
            add("trigger_factor", "有没有明显诱因或加重场景？", ["活动后加重", "进食相关", "夜间明显", "受凉后出现", "不清楚"], "补充诱因和加重因素")
            add("history_medicine", "是否有既往病史、过敏史、正在用药，或已经做过检查？", ["有病史/正在用药", "已有检查报告", "都没有", "不确定"], "补充病史和检查依据")
            add("visit_goal", "这次主要想解决什么问题？", ["首次就诊", "复诊开药", "看检查报告", "想确认挂什么科"], "明确就诊目的")

    red_flag_negative = any(k in text for k in ("没有危险信号", "无危险信号", "没有胸痛", "无胸痛", "没有呼吸困难", "无呼吸困难", "没有一侧无力", "无一侧无力", "没有意识异常", "无意识异常"))
    if not red_flag_negative and not _contains_positive(text, TRIAGE_CRITICAL_SINGLE_KEYWORDS):
        add("red_flag_check", "是否伴有胸痛、呼吸困难、意识异常、大出血、一侧肢体无力等危险信号？", ["没有", "有其中一种", "不确定"], "补充急诊红旗规则")

    compare = build_candidate_comparison(disease_candidates)
    for q in compare.get("distinguish_questions", []):
        add(q["id"], q["question"], q.get("options", []), "用于区分 Top-K 候选疾病")

    confidence = "high"
    if len(symptom_tags) < 2 or missing:
        confidence = "low"
    elif compare.get("need_compare"):
        confidence = "medium"
    if known_disease.get("has_known_disease"):
        confidence = "medium" if not any(q["id"] == "known_disease_evidence" for q in questions) else "high"

    return {
        "needed": bool(questions),
        "confidence": confidence,
        "missing_slots": missing,
        "questions": questions[:8],
        "topk_comparison": compare,
    }


# ============================================================
# 模拟数据（后期替换为数据库接口）
# ============================================================

HOSPITALS = [
    {
        "id": 1, "name": "常州市第一人民医院", "alias": "常州一院",
        "level": "三级甲等", "type": "综合医院",
        "address": "天宁区局前街185号",
        "lat": 31.7768, "lng": 119.9580,
        "phone": "0519-68870000",
        "beds": 2800,
        "daily_outpatients": 8000,
        "departments": ["心血管内科","心脏大血管外科","消化内科","神经内科","神经外科",
            "肝胆胰外科","血液科","肿瘤科","呼吸与危重症医学科","肾内科",
            "风湿免疫科","泌尿外科","骨科","儿科","妇产科","口腔科",
            "耳鼻咽喉科","眼科","介入放射科","内分泌代谢科","皮肤科",
            "感染性疾病科","麻醉科","重症医学科","急诊医学科"],
        "strengths": ["心血管内科","心脏大血管外科","肿瘤科","肝胆胰外科","血液科","神经内科","神经外科"],
        "strength_scores": {"心血管内科": 96, "心脏大血管外科": 98, "肿瘤科": 97, "肝胆胰外科": 96, "血液科": 95, "神经内科": 95, "神经外科": 94, "消化内科": 91, "呼吸与危重症医学科": 90, "肾内科": 88, "风湿免疫科": 87, "泌尿外科": 91, "骨科": 90, "儿科": 89, "妇产科": 88, "介入放射科": 87},
        "rating": 4.7,
        "emergency": True,
        "description": "常州地区规模最大、综合实力最强的三级甲等综合医院，承担着全市及周边地区的医疗、教学、科研任务，已接入498位官网公开医生数据。"
    },
    {
        "id": 2, "name": "常州市第二人民医院", "alias": "常州二院",
        "level": "三级甲等", "type": "综合医院",
        "address": "天宁区兴隆巷29号",
        "lat": 31.7700, "lng": 119.9650,
        "phone": "0519-88104930",
        "beds": 2200,
        "daily_outpatients": 6500,
        "departments": ["心血管内科","消化内科","内分泌科","泌尿外科","普外科","骨科","神经外科",
            "妇产科","儿科","急诊科","呼吸内科","肿瘤科","神经内科","麻醉科","医学影像科"],
        "strengths": ["消化内科","普外科","神经外科","心血管内科","泌尿外科"],
        "strength_scores": {"消化内科": 95, "普外科": 94, "神经外科": 93, "心血管内科": 91, "骨科": 87, "内分泌科": 86, "泌尿外科": 88},
        "rating": 4.5,
        "emergency": True,
        "description": "集医疗、教学、科研为一体的三级甲等综合医院，拥有多个省级重点专科，已接入52位真实医生数据。"
    },
    {
        "id": 3, "name": "常州市中医医院", "alias": "常州中医院",
        "level": "三级甲等", "type": "中医医院",
        "address": "天宁区和平北路25号",
        "lat": 31.7800, "lng": 119.9620,
        "phone": "0519-89896990",
        "beds": 1500,
        "daily_outpatients": 5000,
        "departments": ["心血管科","骨伤科","妇科","肾内科","脾胃病科","肛肠科","肿瘤科","血液肿瘤科",
            "中医内科","针灸推拿科","中医妇科","中医儿科","康复医学科","治未病中心","正骨科"],
        "strengths": ["中医骨伤科","针灸推拿科","中医内科","康复医学科","肾病科"],
        "strength_scores": {"中医骨伤科": 97, "针灸推拿科": 96, "中医内科": 93, "康复医学科": 92, "中医妇科": 88, "肾病科": 90, "心血管科": 91},
        "rating": 4.6,
        "emergency": True,
        "description": "江苏省内规模最大的地市级中医医院，孟河医派传承基地，中医药特色优势突出，已接入264位官网公开医生数据。"
    },
    {
        "id": 4, "name": "常州市第三人民医院", "alias": "常州三院",
        "level": "三级乙等", "type": "综合医院",
        "address": "天宁区兰陵北路300号",
        "lat": 31.7600, "lng": 119.9550,
        "phone": "0519-86666060",
        "beds": 1200,
        "daily_outpatients": 4000,
        "departments": ["传染病科","肝病科","呼吸内科","消化内科","普外科","妇产科"],
        "strengths": ["传染病科","肝病科","呼吸内科"],
        "strength_scores": {"传染病科": 95, "肝病科": 94, "呼吸内科": 88, "消化内科": 82},
        "rating": 4.3,
        "emergency": True,
        "description": "以传染病防治为特色的综合性医院，肝病诊疗中心在省内有较高声誉，已接入147位官网公开医生数据。"
    },
    {
        "id": 5, "name": "常州市肿瘤医院", "alias": "常州四院/肿瘤医院",
        "level": "三级乙等", "type": "专科医院",
        "address": "钟楼区怀德北路1号",
        "lat": 31.7850, "lng": 119.9480,
        "phone": "0519-86867890",
        "beds": 1000,
        "daily_outpatients": 3000,
        "departments": ["中医科","乳腺外科","介入科","儿科","内分泌科","口腔科","呼吸内科","妇产科",
            "心血管内科","放疗科","泌尿外科","消化内科","疼痛科","皮肤性病科","眼科","神经内科",
            "神经外科","耳鼻咽喉头颈外科","肝胆外科","肾内科","肿瘤内科","胃肠外科","胸外科",
            "风湿免疫科","骨科"],
        "strengths": ["肿瘤外科","放疗科","肿瘤内科"],
        "strength_scores": {"肿瘤科": 96, "肿瘤外科": 96, "放疗科": 94, "肿瘤内科": 93, "肿瘤妇科": 89},
        "rating": 4.4,
        "emergency": True,
        "description": "常州地区重要的肿瘤专科与综合诊疗机构，承担全市肿瘤防治任务，已接入133位官网公开医生数据和照片。"
    },
    {
        "id": 6, "name": "常州市儿童医院", "alias": "常州儿童医院",
        "level": "三级甲等", "type": "专科医院",
        "address": "天宁区中吴大道958号",
        "lat": 31.7520, "lng": 119.9550,
        "phone": "0519-69808328",
        "beds": 600,
        "daily_outpatients": 3500,
        "departments": ["呼吸科","新生儿科","消化营养科","神经内科","儿内科","儿外科",
            "儿童保健科","儿童康复科","小儿呼吸科","小儿消化科"],
        "strengths": ["儿内科","新生儿科","小儿呼吸科","神经内科"],
        "strength_scores": {"儿科": 94, "新生儿科": 93, "小儿呼吸科": 91, "儿外科": 88, "神经内科": 89},
        "rating": 4.5,
        "emergency": True,
        "description": "常州及周边地区唯一的儿童专科医院，已接入74位带真人照片的真实医生数据，覆盖呼吸、新生儿、消化、神经等多个专科。"
    },
    {
        "id": 7, "name": "常州市妇幼保健院", "alias": "常州妇幼保健院",
        "level": "三级甲等", "type": "专科医院",
        "address": "钟楼区丁香路16号",
        "lat": 31.7900, "lng": 119.9350,
        "phone": "0519-88581111",
        "beds": 800,
        "daily_outpatients": 4500,
        "departments": ["中医科","乳腺病科","产前诊断","产科","儿保科","儿科","妇保科","妇瘤一科",
            "妇瘤二科","婚前孕前保健科","宫颈疾病诊治中心","心内科","放射科","普妇科","泌尿外科",
            "消化内科","生殖健康科","生殖医学中心","生育技术科","男性科","疼痛科","皮肤科",
            "眼科","神经内科","肝胆外科","胃肠外科","计划生育科","超声科","骨科"],
        "strengths": ["产科","生殖医学科","妇科"],
        "strength_scores": {"产科": 97, "生殖医学科": 95, "妇科": 93, "产前诊断": 90},
        "rating": 4.6,
        "emergency": True,
        "description": "集医疗、保健、教学、科研为一体的三级甲等妇幼保健院，分娩量居全市首位，已接入164位官网公开医生数据和照片。"
    },
    {
        "id": 8, "name": "武进人民医院", "alias": "武进医院",
        "level": "三级乙等", "type": "综合医院",
        "address": "武进区永宁北路2号",
        "lat": 31.7400, "lng": 119.9500,
        "phone": "0519-86312345",
        "beds": 1500,
        "daily_outpatients": 5500,
        "departments": ["心血管内科","骨科","普外科","妇产科","儿科","神经内科","泌尿外科"],
        "strengths": ["骨科","心血管内科","泌尿外科"],
        "strength_scores": {"骨科": 91, "心血管内科": 89, "泌尿外科": 88, "普外科": 85},
        "rating": 4.3,
        "emergency": True,
        "description": "武进区最大的综合性医院，骨科和心血管内科为市级重点专科，已接入515位官网公开医生数据。"
    },
    {
        "id": 9, "name": "金坛第一人民医院", "alias": "金坛医院",
        "level": "三级乙等", "type": "综合医院",
        "address": "金坛区金武路88号",
        "lat": 31.7200, "lng": 119.5800,
        "phone": "0519-82821234",
        "beds": 1000,
        "daily_outpatients": 3500,
        "departments": ["内科","外科","妇产科","儿科","骨科","眼科"],
        "strengths": ["骨科","内科"],
        "strength_scores": {"骨科": 84, "内科": 82, "普外科": 80},
        "rating": 4.1,
        "emergency": True,
        "description": "金坛区最大的综合性医院，承担区域内主要医疗任务。"
    },
    {
        "id": 10, "name": "溧阳市人民医院", "alias": "溧阳医院",
        "level": "三级乙等", "type": "综合医院",
        "address": "溧阳市昆仑北路68号",
        "lat": 31.4100, "lng": 119.4800,
        "phone": "0519-87012345",
        "beds": 1100,
        "daily_outpatients": 3800,
        "departments": ["内科","外科","妇产科","儿科","骨科","神经内科"],
        "strengths": ["神经内科","骨科"],
        "strength_scores": {"神经内科": 85, "骨科": 83, "内科": 81},
        "rating": 4.2,
        "emergency": True,
        "description": "溧阳市最大的综合性医院，神经内科为区域重点学科。"
    },
    {
        "id": 11, "name": "常州市老年病医院", "alias": "常州老年病医院",
        "level": "三级乙等", "type": "综合医院",
        "address": "江苏省常州市延陵东路288号",
        "lat": 31.7870, "lng": 119.9340,
        "phone": "0519-67890099 / 69800509",
        "beds": 600,
        "daily_outpatients": 1800,
        "departments": ["呼吸与重症医学科","烧伤科","精神心理科","肛肠科","神经外科","骨科","皮肤科",
            "妇产科","康复医学科","老年综合科","泌尿外科","乳腺外科","肾内风湿免疫科",
            "胃肠肝胆外科","消化内科","心血管内科","血液肿瘤科","眼科","儿科","神经内科",
            "内分泌代谢科","急诊科","ICU","口腔科","耳鼻咽喉科","放射科","麻醉科",
            "检验科","功能科","针灸推拿科"],
        "strengths": ["老年综合科","康复医学科","呼吸与重症医学科","心血管内科","神经内科","骨科"],
        "strength_scores": {"老年综合科": 90, "康复医学科": 88, "呼吸与重症医学科": 87, "心血管内科": 86, "神经内科": 84, "骨科": 83, "消化内科": 82, "儿科": 80},
        "rating": 4.1,
        "emergency": True,
        "description": "常州市第七人民医院（常州市老年病医院），以老年医学、慢病管理、康复诊疗和综合专科服务为特色，已接入201位官网公开专家数据。"
    },
    {
        "id": 12, "name": "武进中医医院", "alias": "武进区中医医院",
        "level": "三级乙等", "type": "中医医院",
        "address": "武进区湖塘镇",
        "lat": 31.7180, "lng": 119.9440,
        "phone": "暂无",
        "beds": 800,
        "daily_outpatients": 2800,
        "departments": ["中医内科","骨伤科","针灸推拿科","脾胃病科","康复医学科","妇科","儿科"],
        "strengths": ["中医内科","骨伤科","针灸推拿科","康复医学科"],
        "strength_scores": {"中医内科": 88, "骨伤科": 87, "针灸推拿科": 86, "康复医学科": 84},
        "rating": 4.2,
        "emergency": True,
        "description": "武进区域重要的中医医疗机构，提供中医特色诊疗与康复服务。"
    },
    {
        "id": 13, "name": "溧阳市中医医院", "alias": "溧阳中医院",
        "level": "三级乙等", "type": "中医医院",
        "address": "溧阳市",
        "lat": 31.4250, "lng": 119.4870,
        "phone": "暂无",
        "beds": 700,
        "daily_outpatients": 2200,
        "departments": ["中医内科","骨伤科","针灸推拿科","脾胃病科","康复医学科","肾病科"],
        "strengths": ["中医内科","骨伤科","针灸推拿科"],
        "strength_scores": {"中医内科": 86, "骨伤科": 85, "针灸推拿科": 84, "康复医学科": 82},
        "rating": 4.1,
        "emergency": True,
        "description": "溧阳市中医医疗服务核心机构，覆盖中医内科、骨伤、针灸推拿等专科。"
    },
    {
        "id": 14, "name": "常州市德安医院", "alias": "常州德安医院",
        "level": "三级甲等", "type": "专科医院",
        "address": "常州市天宁区",
        "lat": 31.7600, "lng": 119.9750,
        "phone": "暂无",
        "beds": 900,
        "daily_outpatients": 1600,
        "departments": ["司法鉴定","康复中心","心理卫生中心","皮肤科","精神科","综合内科","综合外科","老年科"],
        "strengths": ["精神科","心理科","老年精神科"],
        "strength_scores": {"精神科": 94, "心理科": 90, "老年精神科": 88, "康复医学科": 82},
        "rating": 4.2,
        "emergency": True,
        "description": "以精神卫生、心理诊疗、康复服务和司法鉴定为特色的三级甲等专科医院，已接入42位官网公开医生数据和照片。"
    },
    {
        "id": 15, "name": "常州市第七人民医院", "alias": "戚墅堰区人民医院",
        "level": "二级甲等", "type": "综合医院",
        "address": "经开区/原戚墅堰区",
        "lat": 31.7240, "lng": 120.0580,
        "phone": "暂无",
        "beds": 500,
        "daily_outpatients": 1800,
        "departments": ["内科","外科","妇产科","儿科","骨科","急诊科","康复医学科"],
        "strengths": ["内科","骨科","康复医学科"],
        "strength_scores": {"内科": 78, "骨科": 76, "康复医学科": 75},
        "rating": 4.0,
        "emergency": True,
        "description": "服务经开区及周边居民的二级甲等综合医院。"
    },
    {
        "id": 16, "name": "常州市口腔医院", "alias": "钟楼医院",
        "level": "二级甲等", "type": "专科医院",
        "address": "常州市钟楼区",
        "lat": 31.7790, "lng": 119.9440,
        "phone": "暂无",
        "beds": 300,
        "daily_outpatients": 1800,
        "departments": ["口腔科","口腔颌面外科","牙体牙髓科","牙周科","正畸科","修复科"],
        "strengths": ["口腔科","口腔颌面外科","正畸科"],
        "strength_scores": {"口腔科": 88, "口腔颌面外科": 84, "正畸科": 82, "修复科": 80},
        "rating": 4.2,
        "emergency": False,
        "description": "常州地区口腔专科医疗机构，兼具钟楼医院综合医疗服务。"
    },
    {
        "id": 17, "name": "常州市中西医结合医院", "alias": "广化医院",
        "level": "二级甲等", "type": "中医医院",
        "address": "常州市钟楼区",
        "lat": 31.7720, "lng": 119.9440,
        "phone": "暂无",
        "beds": 450,
        "daily_outpatients": 1700,
        "departments": ["中西医结合科","内科","外科","康复医学科","针灸推拿科","妇科"],
        "strengths": ["中西医结合科","康复医学科","针灸推拿科"],
        "strength_scores": {"中西医结合科": 82, "康复医学科": 80, "针灸推拿科": 78},
        "rating": 4.0,
        "emergency": True,
        "description": "以中西医结合诊疗和社区综合医疗服务为特色的二级甲等医院。"
    },
    {
        "id": 18, "name": "金坛区中医医院", "alias": "金坛中医院",
        "level": "二级甲等", "type": "中医医院",
        "address": "金坛区",
        "lat": 31.7410, "lng": 119.5750,
        "phone": "暂无",
        "beds": 450,
        "daily_outpatients": 1700,
        "departments": ["中医内科","骨伤科","针灸推拿科","康复医学科","脾胃病科","妇科"],
        "strengths": ["中医内科","骨伤科","针灸推拿科"],
        "strength_scores": {"中医内科": 82, "骨伤科": 80, "针灸推拿科": 78},
        "rating": 4.0,
        "emergency": True,
        "description": "金坛区中医药服务主要医疗机构。"
    },
    {
        "id": 19, "name": "金坛区第二人民医院", "alias": "金坛二院",
        "level": "二级医院", "type": "综合医院",
        "address": "金坛区",
        "lat": 31.7270, "lng": 119.5900,
        "phone": "暂无",
        "beds": 350,
        "daily_outpatients": 1300,
        "departments": ["内科","外科","妇产科","儿科","骨科","急诊科"],
        "strengths": ["内科","外科","骨科"],
        "strength_scores": {"内科": 75, "外科": 74, "骨科": 72},
        "rating": 3.9,
        "emergency": True,
        "description": "金坛区区域综合医疗服务机构。"
    },
    {
        "id": 20, "name": "溧阳市妇幼保健院", "alias": "溧阳妇幼保健院",
        "level": "二级甲等", "type": "专科医院",
        "address": "溧阳市",
        "lat": 31.4180, "lng": 119.4920,
        "phone": "暂无",
        "beds": 300,
        "daily_outpatients": 1400,
        "departments": ["产科","妇科","儿科","儿童保健科","妇女保健科","生殖健康科"],
        "strengths": ["产科","妇科","儿童保健科"],
        "strength_scores": {"产科": 80, "妇科": 78, "儿童保健科": 76},
        "rating": 4.0,
        "emergency": True,
        "description": "溧阳市妇女儿童医疗保健服务机构。"
    },
    {
        "id": 21, "name": "新北区三井人民医院", "alias": "三井人民医院",
        "level": "二级医院", "type": "综合医院",
        "address": "新北区三井街道",
        "lat": 31.8180, "lng": 119.9700,
        "phone": "暂无",
        "beds": 250,
        "daily_outpatients": 1200,
        "departments": ["内科","外科","妇产科","儿科","全科医学科","康复医学科"],
        "strengths": ["全科医学科","内科","康复医学科"],
        "strength_scores": {"全科医学科": 74, "内科": 72, "康复医学科": 70},
        "rating": 3.9,
        "emergency": True,
        "description": "新北区基层综合医疗服务机构，服务三井及周边居民。"
    },
]

DOCTORS = [
    {"id": 1, "name": "张文华", "title": "主任医师/教授", "hospital_id": 1, "hospital_name": "常州市第一人民医院",
     "department": "心血管内科", "specialties": ["冠心病介入治疗","高血压","心律失常"],
     "experience": 32,
     "education": "南京医科大学博士", "achievements": ["江苏省医学会心血管分会副主任委员","国家自然科学基金3项"],
     "avatar": "👨‍⚕️"},
    {"id": 2, "name": "李明辉", "title": "主任医师", "hospital_id": 1, "hospital_name": "常州市第一人民医院",
     "department": "神经内科", "specialties": ["脑血管病","帕金森病","癫痫"],
     "experience": 28,
     "education": "复旦大学医学院博士", "achievements": ["中华医学会神经病学分会委员","省科技进步二等奖"],
     "avatar": "👨‍⚕️"},
    {"id": 3, "name": "陈志强", "title": "主任医师/教授", "hospital_id": 1, "hospital_name": "常州市第一人民医院",
     "department": "骨科", "specialties": ["脊柱外科","关节置换","微创骨科"],
     "experience": 30,
     "education": "北京大学医学部博士", "achievements": ["中华医学会骨科分会常委","国家科技进步奖获得者"],
     "avatar": "👨‍⚕️"},
    {"id": 4, "name": "王丽华", "title": "主任医师", "hospital_id": 2, "hospital_name": "常州市第二人民医院",
     "department": "消化内科", "specialties": ["消化道早癌筛查","ERCP","炎症性肠病"],
     "experience": 26,
     "education": "上海交通大学医学院博士", "achievements": ["江苏省消化内镜学会副主任委员","发表SCI论文30余篇"],
     "avatar": "👩‍⚕️"},
    {"id": 5, "name": "赵建国", "title": "主任医师/教授", "hospital_id": 2, "hospital_name": "常州市第二人民医院",
     "department": "神经外科", "specialties": ["脑肿瘤手术","脑血管介入","颅脑损伤"],
     "experience": 29,
     "education": "四川大学华西医学中心博士", "achievements": ["中国医师协会神经外科分会委员","省医学科技一等奖"],
     "avatar": "👨‍⚕️"},
    {"id": 6, "name": "刘雪琴", "title": "主任医师", "hospital_id": 3, "hospital_name": "常州市中医医院",
     "department": "中医骨伤科", "specialties": ["骨折手法复位","颈肩腰腿痛","骨质疏松"],
     "experience": 30,
     "education": "北京中医药大学博士", "achievements": ["全国名老中医学术继承人","省中医药学会骨伤分会主委"],
     "avatar": "👩‍⚕️"},
    {"id": 7, "name": "孙伟", "title": "副主任医师", "hospital_id": 3, "hospital_name": "常州市中医医院",
     "department": "针灸推拿科", "specialties": ["针灸治疗疼痛","推拿正骨","康复理疗"],
     "experience": 18,
     "education": "南京中医药大学硕士", "achievements": ["省针灸学会理事","常州市青年医学人才"],
     "avatar": "👨‍⚕️"},
    {"id": 8, "name": "周美玲", "title": "主任医师/教授", "hospital_id": 5, "hospital_name": "常州市肿瘤医院",
     "department": "肿瘤外科", "specialties": ["乳腺癌手术","甲状腺癌手术","肿瘤微创治疗"],
     "experience": 27,
     "education": "复旦大学上海医学院博士", "achievements": ["中国抗癌协会乳腺癌专业委员会委员","省肿瘤防治先进个人"],
     "avatar": "👩‍⚕️"},
    {"id": 9, "name": "吴国平", "title": "主任医师", "hospital_id": 5, "hospital_name": "常州市肿瘤医院",
     "department": "放疗科", "specialties": ["精确放疗","IMRT","立体定向放疗"],
     "experience": 25,
     "education": "苏州大学医学院博士", "achievements": ["江苏省放射肿瘤学会常委","开展新技术10余项"],
     "avatar": "👨‍⚕️"},
    {"id": 10, "name": "钱晓燕", "title": "主任医师", "hospital_id": 6, "hospital_name": "常州市儿童医院",
     "department": "儿内科", "specialties": ["小儿呼吸系统疾病","儿童哮喘","过敏性紫癜"],
     "experience": 22,
     "education": "上海交通大学医学院博士", "achievements": ["江苏省儿科学会委员","市科技进步奖3项"],
     "avatar": "👩‍⚕️"},
    {"id": 11, "name": "郑海明", "title": "主任医师/教授", "hospital_id": 6, "hospital_name": "常州市儿童医院",
     "department": "新生儿科", "specialties": ["早产儿管理","新生儿窒息","新生儿黄疸"],
     "experience": 28,
     "education": "复旦大学博士", "achievements": ["中华医学会围产医学分会委员","省新生儿学组副组长"],
     "avatar": "👨‍⚕️"},
    {"id": 12, "name": "杨丽萍", "title": "主任医师", "hospital_id": 7, "hospital_name": "常州市妇幼保健院",
     "department": "产科", "specialties": ["高危妊娠管理","妊娠合并症","无痛分娩"],
     "experience": 26,
     "education": "南京医科大学博士", "achievements": ["江苏省围产医学分会副主任委员","年接生量超1000例"],
     "avatar": "👩‍⚕️"},
    {"id": 13, "name": "沈健", "title": "副主任医师", "hospital_id": 7, "hospital_name": "常州市妇幼保健院",
     "department": "生殖医学科", "specialties": ["试管婴儿","人工授精","不孕不育"],
     "experience": 20,
     "education": "北京大学医学部博士", "achievements": ["江苏省生殖医学分会委员","试管婴儿成功率超60%"],
     "avatar": "👨‍⚕️"},
    {"id": 14, "name": "马国强", "title": "主任医师", "hospital_id": 8, "hospital_name": "武进人民医院",
     "department": "骨科", "specialties": ["关节镜手术","运动医学","创伤骨科"],
     "experience": 24,
     "education": "苏州大学医学院硕士", "achievements": ["常州市骨科质量控制中心专家","年手术量超500台"],
     "avatar": "👨‍⚕️"},
    {"id": 15, "name": "黄建华", "title": "主任医师", "hospital_id": 8, "hospital_name": "武进人民医院",
     "department": "心血管内科", "specialties": ["冠心病介入","起搏器植入","心力衰竭"],
     "experience": 25,
     "education": "南京医科大学博士", "achievements": ["常州市心血管病学会委员","PCI年手术量超300例"],
     "avatar": "👨‍⚕️"},
    {"id": 16, "name": "许文斌", "title": "主任医师", "hospital_id": 4, "hospital_name": "常州市第三人民医院",
     "department": "肝病科", "specialties": ["病毒性肝炎","肝硬化","肝衰竭"],
     "experience": 26,
     "education": "南京医科大学博士", "achievements": ["江苏省感染病学分会常委","参与国家重大传染病专项"],
     "avatar": "👨‍⚕️"},
]

# ============================================================
# 加载爬取的真实医生数据
# ============================================================
def _load_real_doctors():
    """从 data/ 目录加载所有医院爬取的真实医生数据"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    all_doctors = []
    all_depts = set()

    # 医院ID → 医院名称映射
    hospital_names = {
        1: "常州市第一人民医院",
        2: "常州市第二人民医院",
        3: "常州市中医医院",
        5: "常州市肿瘤医院",
        6: "常州市儿童医院",
        7: "常州市妇幼保健院",
        14: "常州市德安医院",
    }

    # 加载 data/ 目录下所有 doctors_h*.json 文件
    if os.path.isdir(data_dir):
        for filename in sorted(os.listdir(data_dir)):
            if not filename.startswith("doctors_h") or not filename.endswith(".json"):
                continue
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                hid = data.get("hospital_id", 1)
                hname = data.get("hospital") or hospital_names.get(hid, "未知医院")

                for d in data.get("doctors", []):
                    did = 1000 + hid * 1000 + len([x for x in all_doctors if x["hospital_id"] == hid])
                    rd = {
                        "id": did,
                        "name": d["name"],
                        "title": d.get("title", ""),
                        "hospital_id": hid,
                        "hospital_name": hname,
                        "department": d["department"],
                        "specialties": d.get("keywords", [])[:6],
                        "experience": d.get("experience", 0),
                        "education": d.get("academic_title", ""),
                        "achievements": (d.get("awards", []) or [])[:3] + (d.get("honors", []) or [])[:2],
                        "avatar": "👨‍⚕️" if "女" not in str(d.get("position", "")) else "👩‍⚕️",
                        # 增强字段
                        "surgery_count": d.get("surgery_count"),
                        "surgery_count_note": d.get("surgery_count_note", ""),
                        "sci_papers": d.get("sci_papers"),
                        "total_papers": d.get("total_papers"),
                        "national_funding": d.get("national_funding", False),
                        "patents": d.get("patents"),
                        "keywords": d.get("keywords", []),
                        "academic_title": d.get("academic_title", ""),
                        "position": d.get("position", ""),
                        "specialty": d.get("specialty", ""),
                        "detail": d.get("detail", ""),
                        "outpatient_time": d.get("outpatient_time", ""),
                        "photo_url": d.get("photo_url", ""),
                        "source_image_url": d.get("source_image_url", ""),
                        "doctor_page_url": d.get("doctor_page_url", ""),
                    }
                    all_doctors.append(rd)
                    all_depts.add(d["department"])
                print(f"[数据] {hname}: {len(data.get('doctors',[]))} 位医生, hid={hid}")
            except Exception as e:
                print(f"[数据] 加载 {filename} 失败: {e}")

    # 如果没有 data/ 目录文件，回退到旧版 doctors.json
    if len(all_doctors) == 0:
        json_path = os.path.join(os.path.dirname(__file__), "doctors.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for i, d in enumerate(data.get("doctors", [])):
                rd = {
                    "id": 1000 + i,
                    "name": d["name"],
                    "title": d.get("title", ""),
                    "hospital_id": 1,
                    "hospital_name": "常州市第一人民医院",
                    "department": d["department"],
                    "specialties": d.get("keywords", [])[:6],
                    "experience": d.get("experience", 0),
                    "education": d.get("academic_title", ""),
                    "achievements": (d.get("awards", []) or [])[:3] + (d.get("honors", []) or [])[:2],
                    "avatar": "👨‍⚕️" if "女" not in str(d.get("position", "")) else "👩‍⚕️",
                    "surgery_count": d.get("surgery_count"),
                    "surgery_count_note": d.get("surgery_count_note", ""),
                    "sci_papers": d.get("sci_papers"),
                    "total_papers": d.get("total_papers"),
                    "national_funding": d.get("national_funding", False),
                    "patents": d.get("patents"),
                    "keywords": d.get("keywords", []),
                    "academic_title": d.get("academic_title", ""),
                    "position": d.get("position", ""),
                    "specialty": d.get("specialty", ""),
                    "detail": d.get("detail", ""),
                    "outpatient_time": d.get("outpatient_time", ""),
                    "photo_url": d.get("photo_url", ""),
                    "source_image_url": d.get("source_image_url", ""),
                    "doctor_page_url": d.get("doctor_page_url", ""),
                }
                all_doctors.append(rd)
                all_depts.add(d["department"])
            print(f"[数据] 加载 {len(all_doctors)} 位真实医生, {len(all_depts)} 个科室 (旧版格式)")
        except Exception as e:
            print(f"[数据] 加载 doctors.json 失败: {e}")

    total = len(all_doctors)
    print(f"[数据] 总计加载 {total} 位真实医生, {len(all_depts)} 个科室, {len(set(d['hospital_id'] for d in all_doctors))} 家医院")
    return all_doctors, all_depts

REAL_DOCTORS, REAL_DEPARTMENTS = _load_real_doctors()

def _load_bus_routes():
    """加载常武地区公交线路脱敏数据。"""
    path = os.path.join(os.path.dirname(__file__), "data", "bus_routes.json")
    if not os.path.exists(path):
        print("[数据] 未找到公交线路数据 data/bus_routes.json")
        return {"summary": {}, "routes": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        routes = data.get("routes", [])
        print(f"[数据] 加载公交线路 {len(routes)} 条")
        return {"summary": data.get("summary", {}), "routes": routes}
    except Exception as e:
        print(f"[数据] 加载公交线路数据失败: {e}")
        return {"summary": {}, "routes": []}

BUS_ROUTE_DATA = _load_bus_routes()

def _load_bus_stations():
    """加载常武地区公交站点脱敏数据。"""
    path = os.path.join(os.path.dirname(__file__), "data", "bus_stations.json")
    if not os.path.exists(path):
        print("[数据] 未找到公交站点数据 data/bus_stations.json")
        return {"summary": {}, "stations": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        stations = data.get("stations", [])
        print(f"[数据] 加载公交站点 {len(stations)} 个")
        return {"summary": data.get("summary", {}), "stations": stations}
    except Exception as e:
        print(f"[数据] 加载公交站点数据失败: {e}")
        return {"summary": {}, "stations": []}

BUS_STATION_DATA = _load_bus_stations()

def _load_taxi_operations():
    """加载出租车/网约车运营脱敏样本数据。"""
    path = os.path.join(os.path.dirname(__file__), "data", "taxi_operations.json")
    if not os.path.exists(path):
        print("[数据] 未找到出租车运营数据 data/taxi_operations.json")
        return {"summary": {}, "operations": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        operations = data.get("operations", [])
        print(f"[数据] 加载出租车运营样本 {len(operations)} 条")
        return {"summary": data.get("summary", {}), "operations": operations}
    except Exception as e:
        print(f"[数据] 加载出租车运营数据失败: {e}")
        return {"summary": {}, "operations": []}

TAXI_OPERATION_DATA = _load_taxi_operations()

def _load_bike_stations():
    """加载公共自行车/助力车站点脱敏数据。"""
    path = os.path.join(os.path.dirname(__file__), "data", "bike_stations.json")
    if not os.path.exists(path):
        print("[数据] 未找到公共自行车站点数据 data/bike_stations.json")
        return {"summary": {}, "stations": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        stations = data.get("stations", [])
        print(f"[数据] 加载公共自行车站点 {len(stations)} 个")
        return {"summary": data.get("summary", {}), "stations": stations}
    except Exception as e:
        print(f"[数据] 加载公共自行车站点数据失败: {e}")
        return {"summary": {}, "stations": []}

BIKE_STATION_DATA = _load_bike_stations()

def _load_bike_vehicles():
    """加载共享单车/助力车车辆状态脱敏数据。"""
    path = os.path.join(os.path.dirname(__file__), "data", "bike_vehicles.json")
    if not os.path.exists(path):
        print("[数据] 未找到共享车辆状态数据 data/bike_vehicles.json")
        return {"summary": {}, "vehicles": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        vehicles = data.get("vehicles", [])
        print(f"[数据] 加载共享车辆状态 {len(vehicles)} 条")
        return {"summary": data.get("summary", {}), "vehicles": vehicles}
    except Exception as e:
        print(f"[数据] 加载共享车辆状态数据失败: {e}")
        return {"summary": {}, "vehicles": []}

BIKE_VEHICLE_DATA = _load_bike_vehicles()

def _distance_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1 = math.radians(float(lat1))
    p2 = math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lng2) - float(lng1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _hospital_station_access():
    stations = BUS_STATION_DATA.get("stations", [])
    results = []
    for h in HOSPITALS:
        distances = []
        for s in stations:
            lat = s.get("latitude")
            lng = s.get("longitude")
            if lat is None or lng is None:
                continue
            d = _distance_km(h["lat"], h["lng"], lat, lng)
            distances.append((d, s))
        distances.sort(key=lambda item: item[0])
        nearest = distances[0] if distances else (None, {})
        nearby_2km = [item for item in distances if item[0] <= 2]
        nearby_3km = [item for item in distances if item[0] <= 3]
        score = 35
        if len(nearby_2km) >= 5:
            score = 95
        elif len(nearby_2km) >= 3:
            score = 85
        elif len(nearby_2km) >= 1:
            score = 70
        elif nearest[0] is not None and nearest[0] <= 5:
            score = 55
        results.append({
            "hospital_id": h["id"],
            "hospital_name": h["name"],
            "nearest_station_name": nearest[1].get("station_name", "") if nearest[1] else "",
            "nearest_station_distance_km": round(nearest[0], 2) if nearest[0] is not None else None,
            "nearby_station_count_2km": len(nearby_2km),
            "nearby_station_count_3km": len(nearby_3km),
            "transit_station_score": score,
        })
    return sorted(results, key=lambda item: (item["nearest_station_distance_km"] is None, item["nearest_station_distance_km"] or 999))

def _hospital_taxi_access():
    operations = TAXI_OPERATION_DATA.get("operations", [])
    results = []
    for h in HOSPITALS:
        destination_hits = []
        nearest = None
        for op in operations:
            lat = op.get("dest_latitude")
            lng = op.get("dest_longitude")
            if lat is None or lng is None:
                continue
            d = _distance_km(h["lat"], h["lng"], lat, lng)
            if nearest is None or d < nearest[0]:
                nearest = (d, op)
            if d <= 5:
                destination_hits.append((d, op))

        within_3km = [item for item in destination_hits if item[0] <= 3]
        fares = [item[1].get("fact_price") for item in destination_hits if item[1].get("fact_price") is not None]
        miles = [item[1].get("drive_mile") for item in destination_hits if item[1].get("drive_mile") is not None]
        score = 40
        if len(within_3km) >= 5:
            score = 92
        elif len(within_3km) >= 3:
            score = 82
        elif len(within_3km) >= 1:
            score = 68
        elif nearest and nearest[0] <= 8:
            score = 55

        results.append({
            "hospital_id": h["id"],
            "hospital_name": h["name"],
            "nearby_taxi_destination_count_3km": len(within_3km),
            "nearby_taxi_destination_count_5km": len(destination_hits),
            "nearest_taxi_destination_distance_km": round(nearest[0], 2) if nearest else None,
            "avg_nearby_taxi_fare": round(sum(fares) / len(fares), 2) if fares else 0,
            "avg_nearby_taxi_mile": round(sum(miles) / len(miles), 2) if miles else 0,
            "taxi_access_score": score,
        })
    return sorted(results, key=lambda item: (-item["nearby_taxi_destination_count_3km"], item["nearest_taxi_destination_distance_km"] or 999))

def _hospital_bike_access():
    stations = BIKE_STATION_DATA.get("stations", [])
    results = []
    for h in HOSPITALS:
        distances = []
        for s in stations:
            lat = s.get("latitude")
            lng = s.get("longitude")
            if lat is None or lng is None:
                continue
            d = _distance_km(h["lat"], h["lng"], lat, lng)
            distances.append((d, s))
        distances.sort(key=lambda item: item[0])
        nearest = distances[0] if distances else (None, {})
        nearby_1km = [item for item in distances if item[0] <= 1]
        nearby_2km = [item for item in distances if item[0] <= 2]
        bike_supply_2km = sum(int(item[1].get("bike_num") or 0) for item in nearby_2km)
        e_bike_supply_2km = sum(int(item[1].get("e_bike_num") or 0) for item in nearby_2km)
        lock_supply_2km = sum(int(item[1].get("lock_num") or 0) for item in nearby_2km)
        service_level = 35
        if len(nearby_1km) >= 4 or bike_supply_2km >= 120:
            service_level = 92
        elif len(nearby_1km) >= 2 or bike_supply_2km >= 60:
            service_level = 82
        elif len(nearby_2km) >= 1:
            service_level = 68
        elif nearest[0] is not None and nearest[0] <= 4:
            service_level = 55
        results.append({
            "hospital_id": h["id"],
            "hospital_name": h["name"],
            "nearest_bike_station_name": nearest[1].get("station_name", "") if nearest[1] else "",
            "nearest_bike_station_distance_km": round(nearest[0], 2) if nearest[0] is not None else None,
            "nearby_bike_station_count_1km": len(nearby_1km),
            "nearby_bike_station_count_2km": len(nearby_2km),
            "bike_supply_2km": bike_supply_2km,
            "e_bike_supply_2km": e_bike_supply_2km,
            "lock_supply_2km": lock_supply_2km,
            "bike_service_level": service_level,
        })
    return sorted(results, key=lambda item: (-item["bike_supply_2km"], item["nearest_bike_station_distance_km"] or 999))

def _hospital_bike_vehicle_distribution():
    vehicles = BIKE_VEHICLE_DATA.get("vehicles", [])
    results = []
    for h in HOSPITALS:
        nearby_1km = []
        nearby_2km = []
        for v in vehicles:
            lat = v.get("latitude")
            lng = v.get("longitude")
            if lat is None or lng is None:
                continue
            d = _distance_km(h["lat"], h["lng"], lat, lng)
            if d <= 1:
                nearby_1km.append(v)
            if d <= 2:
                nearby_2km.append(v)
        normal_2km = [v for v in nearby_2km if v.get("bike_state") == "正常"]
        results.append({
            "hospital_id": h["id"],
            "hospital_name": h["name"],
            "nearby_vehicle_count_1km": len(nearby_1km),
            "nearby_vehicle_count_2km": len(nearby_2km),
            "normal_vehicle_count_2km": len(normal_2km),
        })
    return sorted(results, key=lambda item: -item["normal_vehicle_count_2km"])

def _bus_route_stats():
    routes = BUS_ROUTE_DATA.get("routes", [])
    company_counts = {}
    company_bus_counts = {}
    line_type_counts = {}
    ticket_counts = {}
    total_bus = 0
    tickets = []

    for r in routes:
        company = r.get("company") or "未知分公司"
        line_type = r.get("line_type") or "未知类型"
        bus_count = int(r.get("bus_count") or 0)
        ticket = r.get("ticket") or 0

        company_counts[company] = company_counts.get(company, 0) + 1
        company_bus_counts[company] = company_bus_counts.get(company, 0) + bus_count
        line_type_counts[line_type] = line_type_counts.get(line_type, 0) + 1
        total_bus += bus_count

        if ticket:
            tickets.append(float(ticket))
            ticket_key = f"{ticket:g}元"
            ticket_counts[ticket_key] = ticket_counts.get(ticket_key, 0) + 1

    summary = dict(BUS_ROUTE_DATA.get("summary", {}))
    summary.update({
        "total_routes": len(routes),
        "total_bus_count": total_bus,
        "company_count": len(company_counts),
        "line_type_count": len(line_type_counts),
        "avg_ticket": round(sum(tickets) / len(tickets), 2) if tickets else 0,
        "max_bus_route": max(routes, key=lambda r: int(r.get("bus_count") or 0), default={}),
        "company_route_counts": company_counts,
        "company_bus_counts": company_bus_counts,
        "line_type_counts": line_type_counts,
        "ticket_counts": ticket_counts,
        "routes_preview": routes[:8],
        "station_summary": BUS_STATION_DATA.get("summary", {}),
        "taxi_summary": TAXI_OPERATION_DATA.get("summary", {}),
        "bike_summary": BIKE_STATION_DATA.get("summary", {}),
        "bike_vehicle_summary": BIKE_VEHICLE_DATA.get("summary", {}),
        "hospital_station_access": _hospital_station_access(),
        "hospital_taxi_access": _hospital_taxi_access(),
        "hospital_bike_access": _hospital_bike_access(),
        "hospital_bike_vehicle_distribution": _hospital_bike_vehicle_distribution(),
    })
    return summary

# ============================================================
# 增强版推荐引擎 (基于爬取的真实数据 + 动态权重)
# ============================================================
ENHANCED_WEIGHTS = {
    "surgery": {"specialty": 0.31, "surgery": 0.27, "hospital": 0.21, "academic": 0.12, "title": 0.01, "access": 0.08},
    "common": {"specialty": 0.40, "access": 0.32, "hospital": 0.14, "academic": 0.07, "surgery": 0.06, "title": 0.01},
    "complex": {"specialty": 0.39, "academic": 0.28, "hospital": 0.17, "surgery": 0.10, "title": 0.01, "access": 0.05},
    "first_visit": {"specialty": 0.40, "access": 0.28, "hospital": 0.13, "academic": 0.10, "surgery": 0.08, "title": 0.01},
}

RANKING_MODEL_VERSION = "h_triagerank_v1_symptom_disease_penalty"

HOSPITAL_RANKING_WEIGHTS = {
    "emergency": {"clinical": 0.34, "availability": 0.10, "accessibility": 0.14, "continuity": 0.03, "quality": 0.20, "fairness": 0.04, "emergency": 0.15},
    "urgent": {"clinical": 0.38, "availability": 0.11, "accessibility": 0.18, "continuity": 0.05, "quality": 0.18, "fairness": 0.05, "emergency": 0.05},
    "routine": {"clinical": 0.30, "availability": 0.16, "accessibility": 0.27, "continuity": 0.06, "quality": 0.12, "fairness": 0.09, "emergency": 0.00},
    "first_visit": {"clinical": 0.32, "availability": 0.15, "accessibility": 0.24, "continuity": 0.05, "quality": 0.14, "fairness": 0.08, "emergency": 0.02},
}

DOCTOR_EXTRA_WEIGHTS = {
    "surgery": {"availability": 0.04, "continuity": 0.03, "fairness": 0.03},
    "common": {"availability": 0.07, "continuity": 0.04, "fairness": 0.07},
    "complex": {"availability": 0.03, "continuity": 0.04, "fairness": 0.03},
    "first_visit": {"availability": 0.06, "continuity": 0.04, "fairness": 0.05},
}

def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))

def _as_text(value):
    if not value:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(v) for v in value if v)
    return str(value)

def _hospital_for_doctor(doc):
    hid = doc.get("hospital_id")
    return next((h for h in HOSPITALS if h["id"] == hid), None)

def _doctor_title_score(doc):
    title = doc.get("title", "") or ""
    if "主任医师" in title and "副主任" not in title:
        return 1.0
    if "副主任医师" in title:
        return 0.72
    if "主治医师" in title:
        return 0.42
    return 0.25

def _doctor_resource_tier(doc, hospital, specialty_score, academic_score, surgery_score):
    """内部资源分层，不直接向用户展示医生等级。"""
    hospital_text = (hospital or {}).get("level", "")
    title_score = _doctor_title_score(doc)
    strong_platform = "三级甲等" in hospital_text or "三甲" in hospital_text
    high_academic = academic_score >= 0.58 or doc.get("national_funding") or (doc.get("sci_papers") or 0) >= 20
    high_experience = surgery_score >= 0.62 or (doc.get("surgery_count") or 0) >= 800
    if strong_platform and specialty_score >= 0.78 and title_score >= 0.72 and (high_academic or high_experience):
        return "top_expert"
    if specialty_score >= 0.72 and (title_score >= 0.72 or high_experience or high_academic):
        return "expert"
    if specialty_score >= 0.58 or title_score >= 0.42:
        return "specialist"
    return "general"

def _resource_strategy(triage, expert_preference):
    triage = triage or {}
    level = triage.get("level", "routine")
    preference = expert_preference or "system"
    if level == "emergency":
        return {
            "code": "emergency_fast_track",
            "title": "急症优先",
            "visit_path": "急诊优先",
            "expert_preference": preference,
            "expert_enabled": False,
            "top_expert_allowed": True,
            "notice": "当前命中急症红旗，系统不按专家号偏好排序，优先推荐最近急诊能力与120处置。",
        }
    if level == "urgent":
        is_specialty_followup = triage.get("severity_bucket") == "专科病情/需评估" or triage.get("matched_rule") in ("心血管专科病情", "慢病专科随访")
        return {
            "code": "specialty_followup" if is_specialty_followup else "specialty_priority",
            "title": "专科病情 · 专科门诊优先" if is_specialty_followup else "中重症专科优先",
            "visit_path": "专科门诊/必要时专家号" if is_specialty_followup else "专科门诊/专家号",
            "expert_preference": preference,
            "expert_enabled": preference not in ("no_expert",),
            "top_expert_allowed": preference in ("must_expert", "named_followup"),
            "notice": "当前属于明确专科病情，系统提高专科匹配、医院专科能力和连续照护权重；若出现急症红旗请优先急诊。" if is_specialty_followup else "当前病情建议尽快就医，系统提高专科匹配和医院专科能力权重。",
        }
    if preference == "must_expert":
        return {
            "code": "routine_must_expert",
            "title": "普通病症 · 专家号优先",
            "visit_path": "专家号",
            "expert_preference": preference,
            "expert_enabled": True,
            "top_expert_allowed": True,
            "notice": "当前病情倾向普通病症，系统尊重专家号选择，但不建议优先占用顶级专家资源。",
        }
    if preference in ("wish_expert", "named_followup"):
        return {
            "code": "routine_soft_expert",
            "title": "普通病症 · 专家号适度加权",
            "visit_path": "专科门诊/专家号",
            "expert_preference": preference,
            "expert_enabled": True,
            "top_expert_allowed": False,
            "notice": "当前病情倾向普通病症，系统优先推荐科室匹配、距离合适的门诊资源，专家号仅适度加权。",
        }
    return {
        "code": "routine_outpatient",
        "title": "普通病症 · 普通门诊优先",
        "visit_path": "普通门诊",
        "expert_preference": preference,
        "expert_enabled": False,
        "top_expert_allowed": False,
        "notice": "当前病情未触发重症/急症信号，系统降低顶级专家资源占用权重，优先考虑科室匹配、距离和可及门诊资源。",
    }

def _apply_resource_fit(score, tier, triage_level, expert_preference, strategy, access_score):
    adjusted = score
    notes = []
    cap = 1.0
    preference = expert_preference or "system"

    if triage_level == "routine":
        if tier == "top_expert" and not strategy.get("top_expert_allowed"):
            cap = 0.68 if preference in ("system", "no_expert") else 0.76
            adjusted -= 0.16
            notes.append("普通病症降低顶级专家资源占用")
        elif tier == "expert" and preference in ("wish_expert", "must_expert", "named_followup"):
            adjusted += 0.05
            notes.append("已按专家号意图适度加权")
        elif tier in ("general", "specialist") and preference in ("system", "no_expert"):
            adjusted += 0.08 * access_score
            notes.append("普通病症优先匹配可及门诊资源")
        if preference == "must_expert" and tier == "top_expert":
            cap = 0.88
            adjusted -= 0.04
            notes.append("尊重必须专家号选择并保留资源节约提醒")
    elif triage_level == "urgent":
        if tier in ("expert", "top_expert"):
            adjusted += 0.06
            notes.append("中重症提高专科专家适配")
        if tier == "top_expert" and not strategy.get("top_expert_allowed"):
            cap = 0.90
    elif triage_level == "emergency":
        notes.append("急症按急诊能力与距离优先")

    return _clamp(min(adjusted, cap)), notes, cap


def _doctor_resource_mismatch_penalty(doc, hospital, tier, triage_level, expert_preference,
                                      specialty_score, hospital_score, access_score, target_dept):
    """H-TriageRank 医疗资源错配惩罚项。"""
    preference = expert_preference or "system"
    details = []
    total = 0.0

    def add(code, label, value):
        nonlocal total
        if value <= 0:
            return
        value = round(value, 4)
        total += value
        details.append({"code": code, "label": label, "value": value})

    if triage_level == "routine":
        if tier == "top_expert" and preference in ("system", "no_expert", "wish_expert"):
            add("overuse", "普通病症占用顶级专家资源", 0.10 if preference in ("system", "no_expert") else 0.06)
        if access_score < 0.45:
            add("access", "普通病症距离/可达性不优", 0.04)
    elif triage_level == "urgent":
        if tier == "general":
            add("underuse", "较重病情匹配到低层级医生资源", 0.08)
        if hospital_score < 0.58:
            add("underuse", "较重病情对应医院专科能力不足", 0.10)
        if access_score < 0.40:
            add("access", "较重病情到院距离不优", 0.05)
    elif triage_level == "emergency":
        if hospital and not hospital.get("emergency"):
            add("emergency", "急症路径未匹配急诊能力", 0.18)
        if access_score < 0.55:
            add("access", "急症场景到院可达性不足", 0.10)

    if target_dept and specialty_score < 0.55:
        add("specialty", "病症与医生专科方向匹配不足", 0.06)
    if preference == "must_expert" and triage_level == "routine" and tier == "top_expert":
        add("preference", "尊重专家号选择但保留资源分流提醒", 0.03)
    if preference == "no_expert" and triage_level in ("urgent", "emergency") and tier in ("general", "specialist"):
        add("preference", "较重病情下不建议过度降低医生层级", 0.04)

    return _clamp(total, 0.0, 0.30), details

def _departments_related(target_dept, doc_dept):
    if not target_dept or not doc_dept:
        return False
    if target_dept == doc_dept or target_dept in doc_dept or doc_dept in target_dept:
        return True
    families = [
        ("肿瘤",),
        ("消化", "脾胃", "胃肠"),
        ("呼吸", "肺"),
        ("心血管", "心脏"),
        ("神经", "脑"),
        ("骨", "脊柱", "关节"),
        ("妇", "产", "生殖"),
        ("儿", "儿童", "新生儿"),
        ("肾", "泌尿"),
        ("中医", "针灸", "推拿", "康复"),
    ]
    for family in families:
        if any(token in target_dept for token in family) and any(token in doc_dept for token in family):
            return True
    return False

def _hospital_strength_for_dept(hospital, target_dept):
    if not hospital:
        return 0.5
    if not target_dept:
        return 0.6
    scores = hospital.get("strength_scores", {})
    departments = hospital.get("departments", [])
    if target_dept in scores:
        return min(1.0, scores[target_dept] / 100.0)
    if target_dept in departments:
        return 0.75
    for dept, score in scores.items():
        if target_dept in dept or dept in target_dept:
            return min(1.0, score / 100.0)
    for dept in departments:
        if target_dept in dept or dept in target_dept:
            return 0.65
    return 0.5

_TRANSIT_ACCESS_CACHE = None

def _transit_access_maps():
    global _TRANSIT_ACCESS_CACHE
    if _TRANSIT_ACCESS_CACHE is None:
        station_rows = _hospital_station_access()
        taxi_rows = _hospital_taxi_access()
        bike_rows = _hospital_bike_access()
        _TRANSIT_ACCESS_CACHE = {
            "station": {row["hospital_id"]: row for row in station_rows},
            "taxi": {row["hospital_id"]: row for row in taxi_rows},
            "bike": {row["hospital_id"]: row for row in bike_rows},
        }
    return _TRANSIT_ACCESS_CACHE

def _hospital_traffic_access(hospital):
    if not hospital:
        return {
            "station_score": 0.60,
            "taxi_score": 0.60,
            "public_transport_score": 0.60,
            "bike_display_score": 0.0,
            "summary": "暂无交通融合数据",
        }
    maps = _transit_access_maps()
    station = maps["station"].get(hospital["id"], {})
    taxi = maps["taxi"].get(hospital["id"], {})
    bike = maps["bike"].get(hospital["id"], {})
    station_score = _clamp((station.get("transit_station_score") or 60) / 100.0)
    taxi_score = _clamp((taxi.get("taxi_access_score") or 60) / 100.0)
    public_transport_score = _clamp(station_score * 0.55 + taxi_score * 0.45)
    parts = []
    if station.get("nearest_station_name"):
        parts.append(f"最近公交站{station.get('nearest_station_name')}约{station.get('nearest_station_distance_km')}km")
    if station.get("nearby_station_count_2km"):
        parts.append(f"2km内公交站{station.get('nearby_station_count_2km')}个")
    if taxi.get("nearby_taxi_destination_count_3km"):
        parts.append(f"3km内出租车到达样本{taxi.get('nearby_taxi_destination_count_3km')}条")
    return {
        "station_score": round(station_score, 4),
        "taxi_score": round(taxi_score, 4),
        "public_transport_score": round(public_transport_score, 4),
        "nearest_station_name": station.get("nearest_station_name", ""),
        "nearest_station_distance_km": station.get("nearest_station_distance_km"),
        "nearby_station_count_2km": station.get("nearby_station_count_2km", 0),
        "nearby_station_count_3km": station.get("nearby_station_count_3km", 0),
        "nearby_taxi_destination_count_3km": taxi.get("nearby_taxi_destination_count_3km", 0),
        "avg_nearby_taxi_fare": taxi.get("avg_nearby_taxi_fare", 0),
        "avg_nearby_taxi_mile": taxi.get("avg_nearby_taxi_mile", 0),
        "bike_display_score": bike.get("bike_service_level", 0),
        "bike_display_note": "共享骑行仅用于绿色出行展示，不参与医疗推荐排序",
        "summary": "；".join(parts) if parts else "交通样本较少，主要按距离估算可达性",
    }

def _access_score(hospital, user_lat=None, user_lng=None, triage_level="routine"):
    traffic = _hospital_traffic_access(hospital)
    if not hospital or user_lat is None or user_lng is None:
        return traffic["public_transport_score"] * 0.45 + 0.55 * 0.60
    distance = haversine(float(user_lat), float(user_lng), hospital["lat"], hospital["lng"])
    if distance <= 5:
        distance_score = 1.0
    elif distance >= 50:
        distance_score = 0.1
    else:
        distance_score = max(0.1, 1.0 - (distance - 5) * 0.02)
    if triage_level in ("emergency", "urgent"):
        return _clamp(distance_score)
    if triage_level == "first_visit":
        return _clamp(distance_score * 0.56 + traffic["station_score"] * 0.28 + traffic["taxi_score"] * 0.16)
    return _clamp(distance_score * 0.50 + traffic["station_score"] * 0.32 + traffic["taxi_score"] * 0.18)

def _level_score_norm(hospital):
    level = hospital.get("level", "") if hospital else ""
    if level == "三级甲等":
        return 1.0
    if "三级" in level:
        return 0.82
    if "二级甲等" in level:
        return 0.68
    if "二级" in level:
        return 0.58
    return 0.5

def _hospital_district(hospital):
    text = ((hospital or {}).get("address") or "") + " " + ((hospital or {}).get("name") or "")
    for district in ("天宁区", "钟楼区", "武进区", "新北区", "金坛区", "溧阳市", "经开区", "戚墅堰区"):
        if district in text:
            return "经开区" if district == "戚墅堰区" else district
    return "常州市"

def _hospital_availability_score(hospital, triage_level="routine"):
    beds = (hospital or {}).get("beds", 0) or 0
    daily = (hospital or {}).get("daily_outpatients", 0) or 0
    capacity = _clamp(beds / 1800.0)
    if beds and daily:
        crowding = daily / max(1, beds)
        waiting_relief = _clamp(1.15 - crowding / 6.0)
    else:
        waiting_relief = 0.55
    emergency_bonus = 0.12 if hospital and hospital.get("emergency") else 0.0
    if triage_level == "emergency":
        return _clamp(capacity * 0.45 + waiting_relief * 0.30 + emergency_bonus + 0.10)
    return _clamp(capacity * 0.35 + waiting_relief * 0.50 + emergency_bonus)

def _hospital_quality_score(hospital):
    rating = (hospital or {}).get("rating", 4.0) or 4.0
    rating_norm = _clamp(rating / 5.0)
    level_norm = _level_score_norm(hospital)
    return _clamp(rating_norm * 0.58 + level_norm * 0.42)

def _continuity_score(condition, target_dept, hospital):
    text = condition or ""
    continuity_words = ("复诊", "随访", "慢病", "长期", "配药", "术后", "半年", "一年", "老病号")
    if not any(w in text for w in continuity_words):
        return 0.55
    strength = _hospital_strength_for_dept(hospital, target_dept)
    if any(w in text for w in ("慢病", "长期", "配药", "随访")) and hospital and "综合" in hospital.get("type", ""):
        strength = max(strength, 0.70)
    if any(w in text for w in ("康复", "术后")) and hospital and any("康复" in d for d in hospital.get("departments", [])):
        strength = max(strength, 0.78)
    return _clamp(strength)

def _special_population_fit(condition, hospital):
    text = condition or ""
    name = (hospital or {}).get("name", "")
    htype = (hospital or {}).get("type", "")
    score = 0.55
    if any(w in text for w in ("儿童", "小儿", "婴儿", "新生儿")):
        score = 1.0 if "儿童" in name else 0.48
    elif any(w in text for w in ("孕", "产检", "分娩", "胎动", "产后", "妇科", "月经")):
        score = 1.0 if ("妇幼" in name or "妇" in htype or "妇" in name) else 0.55
    elif any(w in text for w in ("肿瘤", "癌", "放疗", "化疗")):
        score = 1.0 if "肿瘤" in name else 0.62
    elif any(w in text for w in ("口腔", "牙", "正畸", "牙周")):
        score = 1.0 if "口腔" in name else 0.45
    elif any(w in text for w in ("中医", "针灸", "推拿", "骨伤", "脾胃")):
        score = 1.0 if "中医" in name or "中医" in htype else 0.65
    elif any(w in text for w in ("老人", "老年", "慢病", "康复")):
        score = 0.95 if ("老年" in name or any("康复" in d for d in hospital.get("departments", []))) else 0.65
    return score

def _fairness_score(condition, hospital, distance, triage_level="routine"):
    level_norm = _level_score_norm(hospital)
    local_bonus = 0.18 if distance <= 8 else (0.10 if distance <= 15 else 0.0)
    level_text = hospital.get("level", "") if hospital else ""
    primary_bonus = 0.0
    if triage_level in ("routine", "first_visit"):
        if "二级" in level_text:
            primary_bonus = 0.18
        elif "三级乙等" in level_text:
            primary_bonus = 0.08
    elif triage_level == "urgent" and "三级" in level_text:
        primary_bonus = 0.06
    fairness = 0.50 + local_bonus + primary_bonus - (0.08 if triage_level in ("routine", "first_visit") and level_norm >= 1.0 else 0)
    return _clamp(fairness)

def _hospital_risk_penalty(condition, target_dept, hospital, triage):
    triage_level = (triage or {}).get("level", "routine")
    penalty = 0.0
    if triage_level == "emergency" and not hospital.get("emergency"):
        penalty += 0.35
    if target_dept:
        matched = _hospital_strength_for_dept(hospital, target_dept)
        if matched < 0.58:
            penalty += 0.10
    population_fit = _special_population_fit(condition, hospital)
    if population_fit < 0.50:
        penalty += 0.12
    return _clamp(penalty, 0.0, 0.45)

def _hospital_recommend_reasons(hospital, feature_scores, distance, matched_dept, triage_level):
    reasons = []
    if matched_dept:
        reasons.append(f"{matched_dept}匹配度{int(feature_scores['clinical'] * 100)}%")
    if distance <= 8:
        reasons.append(f"距离近，约{distance}km")
    elif feature_scores["quality"] >= 0.85:
        reasons.append("医院等级和综合质量较高")
    if feature_scores["availability"] >= 0.72:
        reasons.append("承载能力/就诊可用性较好")
    if triage_level == "emergency" and hospital.get("emergency"):
        reasons.append("具备急诊能力")
    if feature_scores["fairness"] >= 0.70:
        reasons.append("符合分级诊疗与就近可及原则")
    traffic = feature_scores.get("traffic_access") or {}
    if traffic.get("public_transport_score", 0) >= 0.75 and triage_level != "emergency":
        reasons.append("公交/出租车到院可达性较好")
    if not reasons:
        reasons.append("按临床匹配、距离和医院质量综合排序")
    return reasons[:4]

def enhanced_recommend_doctors(condition, scenario="surgery", top_n=5, user_lat=None, user_lng=None, triage=None, expert_preference="system"):
    """
    增强版医生推荐 (使用爬取的真实数据 + 动态权重)
    """
    target_dept = (triage or {}).get("matched_department") or match_department(condition)
    htriage = triage or build_htriage_analysis(condition)
    w = ENHANCED_WEIGHTS.get(scenario, ENHANCED_WEIGHTS["surgery"])
    access_context = "urgent" if scenario == "surgery" else ("first_visit" if scenario == "first_visit" else "routine")
    triage_level = (triage or {}).get("level", "routine")
    strategy = _resource_strategy(triage, expert_preference)

    # 关键词匹配
    query_words = set()
    for word in condition.replace("，", ",").replace("、", ",").split(","):
        query_words.add(word.strip())
    # 症状关键词映射
    for symptom, dept in DISEASE_DEPT_MAP.items():
        if symptom in condition:
            query_words.add(symptom)
    for item in htriage.get("symptom_tags", []):
        query_words.add(item.get("tag", ""))
        for term in item.get("matched_terms", []):
            query_words.add(term)
    for item in htriage.get("disease_candidates", []):
        query_words.add(item.get("name", ""))
        query_words.add(item.get("primary_category", ""))
        query_words.add(item.get("secondary_category", ""))

    results = []
    for doc in REAL_DOCTORS:
        if target_dept:
            # 精确匹配或模糊匹配（如"呼吸内科"包含于"呼吸与危重症医学科"）
            doc_dept = doc["department"]
            if not _departments_related(target_dept, doc_dept):
                continue
        # 无科室匹配时，检查关键词是否命中医生keywords或科室名
        if not target_dept:
            kw_text = _as_text(doc.get("keywords", [])) + " " + doc["department"]
            has_match = any(word in kw_text for word in query_words)
            if not has_match:
                continue

        # (1) 手术经验
        sc = doc.get("surgery_count")
        if sc:
            surgery_score = min(1.0, math.log(sc + 1) / math.log(7000))
        elif doc.get("surgery_count_note"):
            surgery_score = 0.3
        else:
            surgery_score = 0.1

        # (2) 亚专业匹配
        kw_text = _as_text(doc.get("keywords", []))
        hits = sum(1 for word in query_words if word and word in kw_text)
        specialty_score = min(1.0, hits / max(1, len(query_words)) * 2) if query_words else 0.1
        if target_dept and _departments_related(target_dept, doc.get("department", "")):
            specialty_score = max(specialty_score, 0.85)

        # (3) 学术水平
        sci = doc.get("sci_papers", 0) or 0
        total = doc.get("total_papers", 0) or 0
        has_nat = doc.get("national_funding", False)
        has_patent = doc.get("patents", 0) or 0
        academic_raw = min(1.0, sci / 50) * 0.5 + min(1.0, total / 100) * 0.2
        if has_nat: academic_raw += 0.2
        if has_patent: academic_raw += 0.1
        academic_score = min(1.0, academic_raw)

        # (4) 职称头衔：仅作为弱参考项，避免普通病症被高职称强行顶到前列
        title_score = _doctor_title_score(doc)
        honors_text = _as_text(doc.get("achievements", ""))
        if honors_text:
            title_score = min(1.0, title_score + 0.05)

        # (5) 医院/科室平台实力
        hospital = _hospital_for_doctor(doc)
        hospital_score = _hospital_strength_for_dept(hospital, target_dept)

        # (6) 可及性：普通病和初诊更看重距离，重症仅作为低权重辅助项
        access_score = _access_score(hospital, user_lat, user_lng, access_context)
        hospital_distance = None
        if user_lat is not None and user_lng is not None and hospital:
            hospital_distance = haversine(float(user_lat), float(user_lng), hospital["lat"], hospital["lng"])

        base_score = (
            w["surgery"] * surgery_score +
            w["specialty"] * specialty_score +
            w["academic"] * academic_score +
            w["title"] * title_score +
            w["hospital"] * hospital_score +
            w["access"] * access_score
        )

        extra_w = DOCTOR_EXTRA_WEIGHTS.get(scenario, DOCTOR_EXTRA_WEIGHTS["common"])
        availability_score = _hospital_availability_score(hospital, "urgent" if scenario in ("surgery", "complex") else "routine")
        continuity_score = _continuity_score(condition, target_dept, hospital)
        fairness_score = _fairness_score(condition, hospital, 999 if user_lat is None or user_lng is None or not hospital else haversine(float(user_lat), float(user_lng), hospital["lat"], hospital["lng"]), "routine" if scenario in ("common", "first_visit") else "urgent")
        population_fit = _special_population_fit(condition, hospital)
        risk_penalty = 0.0
        if target_dept and hospital_score < 0.58:
            risk_penalty += 0.08
        if population_fit < 0.50:
            risk_penalty += 0.08

        total_score = (
            base_score * (1 - sum(extra_w.values())) +
            extra_w["availability"] * availability_score +
            extra_w["continuity"] * continuity_score +
            extra_w["fairness"] * fairness_score -
            risk_penalty
        )

        if specialty_score > 0.5:
            total_score *= 1.08
        total_score = _clamp(total_score)
        resource_tier = _doctor_resource_tier(doc, hospital, specialty_score, academic_score, surgery_score)
        mismatch_penalty, penalty_details = _doctor_resource_mismatch_penalty(
            doc, hospital, resource_tier, triage_level, expert_preference,
            specialty_score, hospital_score, access_score, target_dept
        )
        total_score = _clamp(total_score - mismatch_penalty)
        total_score, resource_notes, resource_cap = _apply_resource_fit(
            total_score, resource_tier, triage_level, expert_preference, strategy, access_score
        )
        emergency_priority_score = _clamp(total_score * 0.66 + access_score * 0.34)

        explanations = []
        if specialty_score >= 0.85:
            explanations.append("科室/专长匹配")
        if surgery_score >= 0.55:
            explanations.append("临床经验较强")
        if academic_score >= 0.55:
            explanations.append("科研与学术能力较强")
        if access_score >= 0.8:
            explanations.append("距离可及性较好")
        if availability_score >= 0.7:
            explanations.append("医院承载能力较好")
        if penalty_details:
            explanations.append("已应用资源错配惩罚")
        explanations.extend(resource_notes)

        results.append({
            "doctor": doc,
            "match_score": round(total_score, 4),
            "scores": {
                "surgery": round(surgery_score, 4),
                "specialty": round(specialty_score, 4),
                "academic": round(academic_score, 4),
                "title": round(title_score, 4),
                "hospital": round(hospital_score, 4),
                "access": round(access_score, 4),
                "availability": round(availability_score, 4),
                "continuity": round(continuity_score, 4),
                "fairness": round(fairness_score, 4),
                "risk_penalty": round(risk_penalty + mismatch_penalty, 4),
                "mismatch_penalty": round(mismatch_penalty, 4),
            },
            "capability_indices": {
                "DCI": round(specialty_score, 4),
                "CEI": round(surgery_score, 4),
                "ACI": round(academic_score, 4),
                "HCI": round(hospital_score, 4),
                "AAI": round(access_score, 4),
            },
            "penalty_breakdown": penalty_details,
            "matched_dept": target_dept,
            "reasons": explanations[:4] or ["按专科匹配、医生履历和可及性综合排序"],
            "ranking_model": RANKING_MODEL_VERSION,
            "hospital_distance_km": hospital_distance,
            "emergency_priority_score": round(emergency_priority_score, 4),
            "resource_tier": resource_tier,
            "visit_path": strategy.get("visit_path"),
            "resource_cap": round(resource_cap, 4),
        })

    if not results and scenario == "surgery":
        for doc in REAL_DOCTORS:
            hospital = _hospital_for_doctor(doc)
            if not hospital or not hospital.get("emergency"):
                continue
            sc = doc.get("surgery_count")
            if sc:
                surgery_score = min(1.0, math.log(sc + 1) / math.log(7000))
            elif doc.get("surgery_count_note"):
                surgery_score = 0.35
            else:
                surgery_score = 0.18
            title = doc.get("title", "") or ""
            if "主任医师" in title and "副主任" not in title:
                title_score = 1.0
            elif "副主任医师" in title:
                title_score = 0.78
            elif "主治医师" in title:
                title_score = 0.50
            else:
                title_score = 0.34
            access_score = _access_score(hospital, user_lat, user_lng, "urgent")
            quality_score = _hospital_quality_score(hospital)
            availability_score = _hospital_availability_score(hospital, "urgent")
            hospital_distance = None
            if user_lat is not None and user_lng is not None:
                hospital_distance = haversine(float(user_lat), float(user_lng), hospital["lat"], hospital["lng"])
            emergency_priority_score = _clamp(
                access_score * 0.38 +
                title_score * 0.22 +
                quality_score * 0.24 +
                surgery_score * 0.16
            )
            results.append({
                "doctor": doc,
                "match_score": round(emergency_priority_score, 4),
                "scores": {
                    "surgery": round(surgery_score, 4),
                    "specialty": 0.35,
                    "academic": 0.0,
                    "title": round(title_score, 4),
                    "hospital": round(quality_score, 4),
                    "access": round(access_score, 4),
                    "availability": round(availability_score, 4),
                    "continuity": 0.0,
                    "fairness": 0.0,
                    "risk_penalty": 0.0,
                },
                "matched_dept": target_dept,
                "reasons": ["急症兜底召回", "优先支持急诊医院", "综合医生资历与到院距离"],
                "ranking_model": RANKING_MODEL_VERSION,
                "hospital_distance_km": hospital_distance,
                "emergency_priority_score": round(emergency_priority_score, 4),
            })

    if scenario == "surgery":
        results.sort(key=lambda r: -r.get("emergency_priority_score", r["match_score"]))
    else:
        results.sort(key=lambda r: -r["match_score"])
    return results[:top_n]


# 疾病-科室映射
DISEASE_DEPT_MAP = {
    "心脏病": "心血管内科", "冠心病": "心血管内科", "心肌梗死": "心血管内科", "高血压": "心血管内科",
    "心律失常": "心血管内科", "心力衰竭": "心血管内科",
    "胸痛": "心血管内科", "胸闷": "心血管内科", "心慌": "心血管内科",
    "心悸": "心血管内科", "冠脉": "心血管内科", "支架": "心血管内科",
    "脑梗塞": "神经内科", "脑出血": "神经内科", "帕金森": "神经内科",
    "癫痫": "神经内科", "头痛": "神经内科", "头晕": "神经内科",
    "眩晕": "神经内科", "头昏": "神经内科", "站不稳": "神经内科", "走路不稳": "神经内科", "无法站立": "神经内科",
    "骨折": "骨科", "关节炎": "骨科", "颈椎病": "骨科",
    "腰椎间盘突出": "骨科", "骨质疏松": "骨科",
    "腰痛": "骨科", "腰疼": "骨科", "背痛": "骨科", "膝盖": "骨科",
    "关节痛": "骨科", "关节": "骨科", "腿痛": "骨科",
    "脊柱": "骨科", "髋关节": "骨科", "腱鞘": "骨科", "韧带": "骨科",
    "胃癌": "肿瘤科", "肺癌": "肿瘤科", "肝癌": "肿瘤科",
    "乳腺癌": "肿瘤科", "肠癌": "肿瘤科", "食管癌": "肿瘤科",
    "阑尾炎": "普外科", "右下腹痛": "普外科", "右下腹部痛": "普外科", "右下部腹痛": "普外科", "右下腹": "普外科", "右下部": "普外科", "麦氏点": "普外科", "反跳痛": "普外科", "腹肌紧张": "普外科",
    "胃炎": "消化内科", "胃溃疡": "消化内科", "肠炎": "消化内科",
    "胃痛": "消化内科", "反酸": "消化内科", "腹痛": "消化内科",
    "腹泻": "消化内科", "恶心": "消化内科", "呕吐": "消化内科",
    "消化不良": "消化内科", "烧心": "消化内科",
    "肝炎": "消化内科", "肝硬化": "消化内科", "脂肪肝": "消化内科",
    "肺炎": "呼吸与危重症医学科", "哮喘": "呼吸与危重症医学科", "慢阻肺": "呼吸与危重症医学科",
    "感冒": "呼吸内科", "普通感冒": "呼吸内科", "咳嗽": "呼吸内科", "嗓子疼": "呼吸内科", "咽痛": "呼吸内科", "喉咙痛": "呼吸内科", "发热": "呼吸内科",
    "糖尿病": "内分泌代谢科", "甲亢": "内分泌代谢科", "痛风": "内分泌代谢科",
    "肾病": "肾内科", "肾结石": "泌尿外科", "前列腺": "泌尿外科",
    "不孕不育": "妇产科", "产检": "妇产科", "分娩": "妇产科",
    "月经不调": "妇产科", "子宫肌瘤": "妇产科", "卵巢囊肿": "妇产科",
    "小儿感冒": "儿科", "小儿发热": "儿科", "小儿腹泻": "儿科",
    "儿童哮喘": "儿科", "新生儿黄疸": "儿科",
    "中风": "神经内科", "偏瘫": "神经内科", "面瘫": "神经内科",
    "颈椎疼痛": "骨科", "腰腿痛": "骨科", "失眠": "神经内科",
    "焦虑": "精神心理科", "惊恐": "精神心理科", "情绪低落": "精神心理科", "睡眠差": "精神心理科",
    "皮肤": "皮肤科", "皮疹": "皮肤科", "过敏": "皮肤科", "湿疹": "皮肤科",
    "视力": "眼科", "眼睛": "眼科", "白内障": "眼科", "青光眼": "眼科",
    "牙齿": "口腔科", "牙痛": "口腔科", "口腔": "口腔科",
    "听力": "耳鼻咽喉科", "耳鸣": "耳鼻咽喉科", "鼻炎": "耳鼻咽喉科",
    "胆结石": "肝胆胰外科", "胆囊": "肝胆胰外科", "胰腺": "肝胆胰外科",
    "肾衰": "肾内科", "尿毒症": "肾内科", "肾炎": "肾内科",
    # 中医/中西医科室映射
    "骨伤": "骨科", "骨伤科": "骨科", "正骨": "骨科",
    "脾胃": "消化内科", "脾胃病": "消化内科",
    "肛肠": "肛肠科", "痔疮": "肛肠科", "肛瘘": "肛肠科",
    # 儿科细分
    "新生儿": "新生儿科", "早产": "新生儿科",
    "儿童": "儿科", "小儿": "儿科",
    # 妇产科细分
    "月经": "妇科", "不孕": "生殖医学科", "更年期": "妇科",
    "子宫肌瘤": "妇科", "卵巢": "妇科", "宫颈": "妇科",
    "产科": "产科", "分娩": "产科", "产后": "产科",
    "怀孕": "产科", "孕期": "产科", "孕妇": "产科", "孕期出血": "产科", "胎动减少": "产科",
    # 急诊/危重信号
    "意识不清": "急诊医学科", "昏迷": "急诊医学科", "休克": "急诊医学科",
    "抽搐": "急诊医学科", "惊厥": "急诊医学科", "严重过敏": "急诊医学科",
    "自杀": "精神心理科", "轻生": "精神心理科",
    # 其他
    "中医": "中医内科", "针灸": "针灸推拿科", "推拿": "针灸推拿科",
}

# 扩展疾病知识库：用于识别用户直接输入的具体病名，并映射到更合适的首诊科室。
# 这层只负责“病名-科室”召回；是否急症仍由红旗规则和严重程度规则决定。
DISEASE_DEPT_MAP.update({
    "心肌炎": "心血管内科", "心包炎": "心血管内科", "房颤": "心血管内科", "心房颤动": "心血管内科",
    "早搏": "心血管内科", "室上速": "心血管内科", "心动过速": "心血管内科", "心动过缓": "心血管内科",
    "心瓣膜病": "心血管内科", "瓣膜病": "心血管内科", "先天性心脏病": "心血管内科", "先心病": "心血管内科",
    "动脉硬化": "心血管内科", "主动脉夹层": "急诊医学科", "肺动脉高压": "心血管内科", "心肌缺血": "心血管内科",
    "心绞痛": "心血管内科", "冠状动脉粥样硬化": "心血管内科",

    "支气管炎": "呼吸内科", "急性支气管炎": "呼吸内科", "慢性支气管炎": "呼吸内科", "支气管扩张": "呼吸内科",
    "肺结节": "呼吸内科", "肺部结节": "呼吸内科", "肺气肿": "呼吸内科", "肺栓塞": "急诊医学科",
    "肺结核": "感染性疾病科", "胸膜炎": "呼吸内科", "间质性肺炎": "呼吸与危重症医学科", "气胸": "胸外科",
    "过敏性鼻炎": "耳鼻咽喉科", "鼻窦炎": "耳鼻咽喉科", "咽炎": "耳鼻咽喉科", "扁桃体炎": "耳鼻咽喉科",

    "胃食管反流": "消化内科", "反流性食管炎": "消化内科", "胃肠炎": "消化内科", "急性胃肠炎": "消化内科",
    "肠梗阻": "普外科", "胆囊炎": "肝胆胰外科", "胆管炎": "肝胆胰外科", "胰腺炎": "肝胆胰外科", "急性胰腺炎": "急诊医学科",
    "乙肝": "感染性疾病科", "丙肝": "感染性疾病科", "肝功能异常": "消化内科", "胃息肉": "消化内科", "肠息肉": "消化内科",
    "肛裂": "肛肠科", "便秘": "消化内科", "便血": "肛肠科", "黑便": "消化内科",

    "脑梗": "神经内科", "脑卒中": "神经内科", "卒中": "神经内科", "短暂性脑缺血发作": "神经内科", "TIA": "神经内科",
    "偏头痛": "神经内科", "眩晕症": "神经内科", "前庭神经炎": "神经内科", "阿尔茨海默病": "神经内科", "老年痴呆": "神经内科",
    "周围神经病": "神经内科", "三叉神经痛": "神经内科", "面神经炎": "神经内科", "脑膜炎": "神经内科",

    "甲减": "内分泌代谢科", "甲状腺功能减退": "内分泌代谢科", "甲状腺结节": "甲乳外科", "甲状腺炎": "内分泌代谢科",
    "高尿酸血症": "内分泌代谢科", "尿酸高": "内分泌代谢科", "高脂血症": "内分泌代谢科", "血脂高": "内分泌代谢科",
    "肥胖症": "内分泌代谢科", "低血糖": "内分泌代谢科", "类风湿关节炎": "风湿免疫科", "系统性红斑狼疮": "风湿免疫科",
    "强直性脊柱炎": "风湿免疫科", "干燥综合征": "风湿免疫科",

    "慢性肾病": "肾内科", "慢性肾脏病": "肾内科", "肾功能不全": "肾内科", "急性肾损伤": "肾内科",
    "尿路感染": "泌尿外科", "膀胱炎": "泌尿外科", "前列腺炎": "泌尿外科", "前列腺增生": "泌尿外科",
    "输尿管结石": "泌尿外科", "膀胱结石": "泌尿外科", "肾积水": "泌尿外科", "尿失禁": "泌尿外科",

    "阴道炎": "妇科", "盆腔炎": "妇科", "宫颈炎": "妇科", "宫颈糜烂": "妇科", "子宫内膜异位症": "妇科",
    "多囊卵巢综合征": "妇科", "宫外孕": "急诊医学科", "异位妊娠": "急诊医学科", "乳腺增生": "甲乳外科", "乳腺结节": "甲乳外科",
    "乳腺炎": "甲乳外科", "产后出血": "产科",

    "小儿肺炎": "儿科", "儿童肺炎": "儿科", "手足口病": "儿科", "川崎病": "儿科", "小儿哮喘": "儿科",
    "儿童腹泻": "儿科", "小儿支气管炎": "儿科", "儿童过敏": "儿科", "儿童鼻炎": "儿科", "小儿惊厥": "儿科",

    "皮炎": "皮肤科", "荨麻疹": "皮肤科", "银屑病": "皮肤科", "牛皮癣": "皮肤科", "痤疮": "皮肤科",
    "带状疱疹": "皮肤科", "足癣": "皮肤科", "灰指甲": "皮肤科", "毛囊炎": "皮肤科", "玫瑰痤疮": "皮肤科",

    "肩周炎": "骨科", "腱鞘炎": "骨科", "滑膜炎": "骨科", "半月板损伤": "骨科", "韧带损伤": "骨科",
    "腰肌劳损": "骨科", "骨关节炎": "骨科", "颈肩腰腿痛": "骨科", "痛风性关节炎": "风湿免疫科",

    "中耳炎": "耳鼻咽喉科", "耳石症": "耳鼻咽喉科", "突发性耳聋": "耳鼻咽喉科", "声带息肉": "耳鼻咽喉科",
    "近视": "眼科", "干眼症": "眼科", "结膜炎": "眼科", "角膜炎": "眼科", "视网膜脱落": "眼科",
    "牙周炎": "口腔科", "龋齿": "口腔科", "智齿": "口腔科", "口腔溃疡": "口腔科", "牙龈炎": "口腔科",

    "结直肠癌": "肿瘤科", "大肠癌": "肿瘤科", "甲状腺癌": "甲乳外科", "淋巴瘤": "血液科", "白血病": "血液科",
    "鼻咽癌": "肿瘤科", "胰腺癌": "肿瘤科", "宫颈癌": "妇科", "卵巢癌": "妇科", "前列腺癌": "泌尿外科",
})



# 医疗小助手分诊知识规则
# 规则来源参考 CDC/Mayo/NHS 等公开急症识别建议，落地为可解释的关键词规则。
TRIAGE_RED_FLAGS = [
    {
        "name": "疑似心血管急症",
        "dept": "心血管内科",
        "keywords": ["胸痛", "胸闷", "心前区痛", "压榨感", "冠脉", "心梗", "心肌梗死"],
        "with_any": ["呼吸困难", "气短", "大汗", "出冷汗", "恶心", "呕吐", "头晕", "晕厥", "放射痛", "左肩痛", "背痛"],
        "advice": "出现胸痛/胸闷并伴随呼吸困难、大汗、晕厥等表现时，应优先急诊评估。",
    },
    {
        "name": "疑似卒中/神经急症",
        "dept": "神经内科",
        "keywords": ["中风", "卒中", "脑梗", "脑梗塞", "脑出血", "偏瘫", "口角歪斜", "说话不清", "言语不清", "一侧无力", "肢体麻木", "站不稳", "走路不稳", "无法站立", "天旋地转"],
        "with_any": ["突然", "急性", "头晕", "眩晕", "恶心", "呕吐", "想吐", "意识不清", "视物模糊", "剧烈头痛"],
        "advice": "突发口角歪斜、肢体无力、言语不清等卒中信号，应尽快急诊处理。",
    },
    {
        "name": "呼吸困难/低氧风险",
        "dept": "呼吸与危重症医学科",
        "keywords": ["呼吸困难", "喘不上气", "气短", "憋气", "紫绀", "嘴唇发紫", "血氧低"],
        "with_any": ["胸痛", "高热", "意识不清", "哮喘", "肺炎", "咯血"],
        "advice": "明显呼吸困难、发绀或血氧异常时，应优先急诊或呼吸危重症评估。",
    },
    {
        "name": "急腹症风险",
        "dept": "普外科",
        "keywords": ["剧烈腹痛", "严重腹痛", "急腹痛", "腹痛难忍", "腹部剧痛", "阑尾炎", "右下腹痛", "右下腹部痛", "右下部腹痛", "右下腹", "右下部", "麦氏点", "反跳痛"],
        "with_any": ["发热", "便血", "黑便", "呕血", "持续呕吐", "腹胀", "压痛", "反跳痛", "腹肌紧张", "怀孕", "外伤"],
        "advice": "剧烈腹痛合并发热、便血、持续呕吐、腹胀或外伤等情况，应尽快急诊评估。",
    },
    {
        "name": "严重外伤/出血",
        "dept": "急诊医学科",
        "keywords": ["严重外伤", "车祸", "摔伤后昏迷", "大量出血", "止不住血", "开放性骨折"],
        "with_any": [],
        "advice": "严重外伤、大量出血或意识异常应立即急诊处理。",
    },
    {
        "name": "意识障碍/持续抽搐",
        "dept": "急诊医学科",
        "keywords": ["意识不清", "昏迷", "呼之不应", "休克", "抽搐不止", "持续抽搐", "惊厥不止"],
        "with_any": [],
        "advice": "意识不清、昏迷、休克或抽搐持续不缓解属于高风险情况，应立即急诊/急救处理。",
    },
    {
        "name": "严重过敏/窒息风险",
        "dept": "急诊医学科",
        "keywords": ["过敏性休克", "喉头水肿", "喉咙肿", "吞咽困难", "喘鸣", "窒息", "全身风团"],
        "with_any": ["呼吸困难", "胸闷", "嘴唇发紫", "头晕", "晕厥", "血压低"],
        "advice": "过敏后出现呼吸困难、喉咙肿、晕厥或疑似休克时，应立即急诊/急救处理。",
    },
    {
        "name": "孕产急症风险",
        "dept": "产科",
        "keywords": ["孕期出血", "孕妇出血", "阴道大量出血", "胎动减少", "羊水破了", "破水", "孕妇剧烈腹痛"],
        "with_any": [],
        "advice": "孕期出血、胎动明显减少、破水或剧烈腹痛应优先产科急诊评估。",
    },
    {
        "name": "儿童危重信号",
        "dept": "儿科",
        "keywords": ["婴儿高热", "儿童高热", "小儿高热", "高热惊厥", "小儿抽搐", "儿童抽搐", "精神萎靡", "反应差"],
        "with_any": [],
        "advice": "婴幼儿或儿童出现高热伴抽搐、精神萎靡、反应差等表现时，应尽快急诊或儿科急诊评估。",
    },
    {
        "name": "心理危机/自伤风险",
        "dept": "精神心理科",
        "keywords": ["自杀", "轻生", "想死", "伤害自己", "自残", "服药自杀", "割腕"],
        "with_any": [],
        "advice": "出现自杀、自伤或伤害他人的想法/行为时，应立即联系家属并寻求急诊或精神心理危机干预。",
    },
    {
        "name": "突发视力/眼外伤急症",
        "dept": "眼科",
        "keywords": ["突然失明", "突发失明", "视力突然下降", "眼外伤", "眼球破裂", "化学品进眼"],
        "with_any": [],
        "advice": "突发视力下降、眼外伤或化学品入眼需要尽快眼科急诊评估。",
    },
]

TRIAGE_URGENT_KEYWORDS = [
    "高烧", "高热", "持续发热", "反复发热", "持续呕吐", "脱水", "咯血", "便血", "黑便",
    "血尿", "骨折", "剧烈疼痛", "疼痛加重", "感染", "化脓", "红肿热痛", "孕期出血",
    "新生儿", "婴儿", "老人", "基础病", "糖尿病足", "39度", "40度", "发烧三天",
    "持续腹泻", "尿不出", "尿潴留", "黄疸加重", "伤口感染", "术后发热", "术后出血",
    "胸痛", "胸闷气短", "喘不上气", "气短明显", "意识模糊", "肢体无力", "一侧麻木",
    "说话不清", "口角歪斜", "突然头痛", "站不稳", "无法站立", "走路不稳", "天旋地转", "腹痛难忍", "右下腹痛", "右下腹部痛", "右下部腹痛", "阑尾炎", "反跳痛", "腹肌紧张", "疼痛难忍",
    "肿瘤", "癌", "癌症", "占位", "放疗", "化疗", "疑似肿瘤", "怀疑肿瘤",
    "肺栓塞", "主动脉夹层", "急性胰腺炎", "肠梗阻", "宫外孕", "异位妊娠", "脑膜炎", "视网膜脱落", "突发性耳聋",
]

TRIAGE_SPECIALTY_DISEASE_RULES = [
    {"name": "心血管专科病情", "dept": "心血管内科", "keywords": ["心脏病", "冠心病", "心绞痛", "心肌缺血", "心律失常", "心力衰竭", "心衰", "房颤", "早搏", "心肌炎", "心包炎", "心瓣膜病", "先心病", "冠脉支架", "装支架", "高血压"], "advice": "已明确提到心血管疾病方向，未命中急症红旗时按心血管专科门诊优先评估；若出现胸痛、大汗、晕厥或呼吸困难，应立即急诊。"},
    {"name": "呼吸专科病情", "dept": "呼吸内科", "keywords": ["慢阻肺", "哮喘", "支气管扩张", "慢性支气管炎", "肺结节", "肺部结节", "肺气肿", "胸膜炎", "间质性肺炎", "肺结核"], "advice": "已明确提到呼吸系统专科病名，建议按呼吸专科门诊评估；如明显喘不上气、嘴唇发紫、血氧低或咯血，应优先急诊。"},
    {"name": "神经专科病情", "dept": "神经内科", "keywords": ["癫痫", "帕金森", "偏头痛", "眩晕症", "面瘫", "面神经炎", "阿尔茨海默", "老年痴呆", "周围神经病", "三叉神经痛", "脑梗", "脑梗塞", "脑卒中后遗症"], "advice": "已明确提到神经系统专科病名，建议神经内科评估；若突然口角歪斜、一侧无力、说话不清或意识异常，应立即急诊。"},
    {"name": "内分泌代谢慢病", "dept": "内分泌代谢科", "keywords": ["糖尿病", "甲亢", "甲减", "甲状腺功能减退", "甲状腺结节", "痛风", "高尿酸", "高尿酸血症", "高脂血症", "血脂高", "肥胖症", "低血糖", "骨质疏松"], "advice": "已明确提到内分泌或代谢慢病，建议内分泌代谢科规范评估、用药调整或随访，不按普通小病处理。"},
    {"name": "肾脏泌尿专科病情", "dept": "肾内科", "keywords": ["慢性肾病", "慢性肾脏病", "肾病", "肾炎", "肾衰", "肾功能不全", "尿毒症", "肾结石", "输尿管结石", "尿路感染", "前列腺炎", "前列腺增生"], "advice": "已明确提到肾脏或泌尿系统疾病，建议对应专科评估；若尿不出、剧烈腰腹痛、发热寒战或肉眼血尿，应尽快就医。"},
    {"name": "消化肝胆专科病情", "dept": "消化内科", "keywords": ["胃溃疡", "胃食管反流", "反流性食管炎", "肝炎", "乙肝", "丙肝", "肝硬化", "脂肪肝", "胆囊炎", "胆结石", "胰腺炎", "肠梗阻", "胃息肉", "肠息肉"], "advice": "已明确提到消化、肝胆或胰腺疾病，建议消化/肝胆专科评估；若剧烈腹痛、黑便、呕血或持续呕吐，应优先急诊。"},
    {"name": "妇产乳腺专科病情", "dept": "妇科", "keywords": ["阴道炎", "盆腔炎", "子宫肌瘤", "卵巢囊肿", "宫颈炎", "多囊卵巢", "子宫内膜异位症", "乳腺增生", "乳腺结节", "乳腺炎", "不孕不育"], "advice": "已明确提到妇科、产科或乳腺相关疾病，建议对应专科门诊评估；孕期出血、剧烈腹痛或胎动减少需优先急诊。"},
    {"name": "肿瘤血液专科病情", "dept": "肿瘤科", "keywords": ["肺癌", "胃癌", "肝癌", "乳腺癌", "肠癌", "结直肠癌", "甲状腺癌", "淋巴瘤", "白血病", "鼻咽癌", "胰腺癌", "宫颈癌", "卵巢癌", "前列腺癌", "肿瘤", "癌症", "占位"], "advice": "已明确提到肿瘤或血液系统疾病，建议按肿瘤/血液/对应器官专科评估，优先考虑连续诊疗和报告复核。"},
    {"name": "儿科专科病情", "dept": "儿科", "keywords": ["小儿肺炎", "儿童肺炎", "小儿哮喘", "儿童哮喘", "手足口病", "川崎病", "小儿腹泻", "儿童腹泻", "新生儿黄疸", "小儿惊厥"], "advice": "已明确提到儿童专科疾病，建议优先儿科评估；婴幼儿高热、抽搐、精神萎靡或反应差需尽快急诊。"},
    {"name": "皮肤骨科五官常见专科病情", "dept": "全科医学科", "keywords": ["湿疹", "皮炎", "荨麻疹", "银屑病", "痤疮", "带状疱疹", "颈椎病", "腰椎间盘突出", "肩周炎", "腱鞘炎", "鼻炎", "鼻窦炎", "中耳炎", "白内障", "青光眼", "牙周炎", "龋齿"], "advice": "已明确提到常见专科病名，建议按对应专科门诊评估；若疼痛剧烈、外伤、视力突降或感染扩散，应及时就医。"},
]

TRIAGE_CRITICAL_SINGLE_KEYWORDS = [
    "呼吸困难", "喘不上气", "无法呼吸", "憋气明显", "嘴唇发紫", "紫绀", "血氧低",
    "昏迷", "意识不清", "呼之不应", "休克", "大出血", "大量出血", "止不住血",
    "偏瘫", "一侧无力", "口角歪斜", "说话不清", "言语不清", "抽搐不止", "无法站立",
    "肺栓塞", "主动脉夹层", "宫外孕", "异位妊娠", "视网膜脱落",
]

TRIAGE_SEVERE_MODIFIERS = [
    "严重", "剧烈", "难忍", "突然", "急性", "持续", "持续加重", "明显加重",
    "不能", "无法", "大汗", "出冷汗", "晕厥", "濒死感",
]

TRIAGE_MILD_KEYWORDS = [
    "有点", "轻微", "偶尔", "轻度", "感冒", "普通感冒", "流鼻涕", "鼻塞", "低热", "轻微咳嗽",
    "皮肤瘙痒", "复诊", "体检", "配药", "慢性病随访", "半年", "长期", "慢性",
    "打喷嚏", "咽痛", "嗓子疼", "轻微腹泻", "轻微扭伤", "痘痘", "痤疮",
]


def _contains_any(text, words):
    return any(w and w in text for w in words)


def _contains_positive(text, words):
    neg_prefixes = ("无", "没有", "没", "未", "否认", "不伴", "未见")
    neg_breakers = ("但", "但是", "不过", "然而", "却", "仍", "仍然", "伴", "伴有", "出现")
    hard_boundaries = "。！？；;\n\r"

    def is_negated(start):
        window_start = max(0, start - 16)
        prefix = text[window_start:start]
        for mark in hard_boundaries:
            idx = prefix.rfind(mark)
            if idx != -1:
                prefix = prefix[idx + 1:]
        neg_pos = max(prefix.rfind(neg) for neg in neg_prefixes)
        if neg_pos == -1:
            return False
        tail = prefix[neg_pos:]
        if any(br in tail for br in neg_breakers):
            return False
        return len(tail) <= 14

    for word in words:
        if not word:
            continue
        start = text.find(word)
        while start != -1:
            if not is_negated(start):
                return True
            start = text.find(word, start + len(word))
    return False

HTRIAGE_NOTICE = "疾病候选与病类判断仅用于就医推荐参考，不作为诊断结果。"

STANDARD_SYMPTOM_RULES = [
    {"tag": "胸痛/胸闷", "aliases": ["胸痛", "胸闷", "心前区痛", "压榨感", "胸口痛"], "system": "心血管系统", "disease": "心绞痛/急性冠脉综合征风险", "primary": "心血管疾病", "secondary": "心血管急症风险", "dept": "心血管内科", "score": 0.88, "red": True},
    {"tag": "心悸", "aliases": ["心悸", "心慌", "心跳快", "心律失常", "早搏"], "system": "心血管系统", "disease": "心律失常", "primary": "心血管疾病", "secondary": "心律失常相关", "dept": "心血管内科", "score": 0.72},
    {"tag": "呼吸困难", "aliases": ["呼吸困难", "喘不上气", "气短", "憋气", "无法呼吸", "嘴唇发紫"], "system": "呼吸系统", "disease": "哮喘/肺炎或低氧风险", "primary": "呼吸系统疾病", "secondary": "呼吸系统急症风险", "dept": "呼吸与危重症医学科", "score": 0.90, "red": True},
    {"tag": "咳嗽咳痰", "aliases": ["咳嗽", "咳痰", "痰多", "干咳", "黄痰", "咯血"], "system": "呼吸系统", "disease": "支气管炎/肺部感染", "primary": "呼吸系统疾病", "secondary": "呼吸系统感染", "dept": "呼吸内科", "score": 0.66},
    {"tag": "发热", "aliases": ["发热", "发烧", "高烧", "高热", "低热", "寒战"], "system": "感染/全身症状", "disease": "感染性疾病/流感样症状", "primary": "感染性疾病", "secondary": "发热感染类", "dept": "感染性疾病科", "score": 0.62},
    {"tag": "鼻塞流涕", "aliases": ["鼻塞", "流鼻涕", "打喷嚏", "咽痛", "嗓子疼", "喉咙痛"], "system": "呼吸系统", "disease": "普通上呼吸道感染", "primary": "呼吸系统疾病", "secondary": "呼吸系统普通病", "dept": "呼吸内科", "score": 0.58},
    {"tag": "腹痛", "aliases": ["腹痛", "肚子疼", "胃痛", "胃疼", "剧烈腹痛", "腹痛难忍"], "system": "消化系统", "disease": "胃肠炎/急腹症风险", "primary": "消化系统疾病", "secondary": "消化系统疼痛类", "dept": "消化内科", "score": 0.70},
    {"tag": "右下腹/阑尾区疼痛", "aliases": ["阑尾炎", "右下腹痛", "右下腹部痛", "右下部腹痛", "右下腹", "右下部", "麦氏点", "反跳痛", "腹肌紧张"], "system": "消化/外科系统", "disease": "阑尾炎/急腹症外科风险", "primary": "外科急腹症", "secondary": "右下腹疼痛类", "dept": "普外科", "score": 0.82, "red": True},
    {"tag": "腹泻呕吐", "aliases": ["腹泻", "拉肚子", "呕吐", "恶心", "持续呕吐", "脱水"], "system": "消化系统", "disease": "急性胃肠炎/脱水风险", "primary": "消化系统疾病", "secondary": "消化系统感染类", "dept": "消化内科", "score": 0.66},
    {"tag": "头痛头晕", "aliases": ["头痛", "头晕", "眩晕", "头昏", "天旋地转", "头晕想吐", "站不稳", "走路不稳", "无法站立", "剧烈头痛", "突然头痛"], "system": "神经系统", "disease": "眩晕/神经系统风险", "primary": "神经系统疾病", "secondary": "神经系统眩晕类", "dept": "神经内科", "score": 0.76},
    {"tag": "肢体无力/言语异常", "aliases": ["偏瘫", "一侧无力", "肢体无力", "口角歪斜", "说话不清", "言语不清"], "system": "神经系统", "disease": "脑卒中风险", "primary": "神经系统疾病", "secondary": "神经系统急症风险", "dept": "神经内科", "score": 0.92, "red": True},
    {"tag": "关节/骨骼疼痛", "aliases": ["骨折", "关节痛", "腰痛", "腰疼", "背痛", "膝盖痛", "颈椎痛", "腿痛"], "system": "运动系统", "disease": "骨关节疾病/外伤", "primary": "骨科疾病", "secondary": "骨关节疼痛类", "dept": "骨科", "score": 0.68},
    {"tag": "皮疹瘙痒", "aliases": ["皮疹", "皮肤瘙痒", "过敏", "湿疹", "红疹", "风团", "痘痘", "痤疮"], "system": "皮肤系统", "disease": "皮炎湿疹/过敏反应", "primary": "皮肤免疫疾病", "secondary": "皮肤普通病", "dept": "皮肤科", "score": 0.62},
    {"tag": "孕产异常", "aliases": ["怀孕", "孕期", "孕妇", "孕期出血", "胎动减少", "破水", "产后"], "system": "妇产系统", "disease": "妊娠相关风险", "primary": "妇产科疾病", "secondary": "孕产风险类", "dept": "产科", "score": 0.82, "red": True},
    {"tag": "儿童症状", "aliases": ["儿童", "小儿", "婴儿", "新生儿", "小孩", "宝宝"], "system": "儿科系统", "disease": "儿童常见病/儿童急症风险", "primary": "儿科疾病", "secondary": "儿童专科病类", "dept": "儿科", "score": 0.76},
    {"tag": "肿瘤相关", "aliases": ["肿瘤", "癌", "癌症", "放疗", "化疗", "占位"], "system": "肿瘤系统", "disease": "肿瘤相关疾病", "primary": "肿瘤疾病", "secondary": "肿瘤专科病类", "dept": "肿瘤科", "score": 0.84},
    {"tag": "泌尿症状", "aliases": ["尿痛", "尿频", "尿急", "血尿", "尿不出", "肾结石", "前列腺"], "system": "泌尿系统", "disease": "泌尿系统感染/结石", "primary": "泌尿系统疾病", "secondary": "泌尿系统常见病", "dept": "泌尿外科", "score": 0.66},
    {"tag": "代谢异常", "aliases": ["糖尿病", "血糖高", "甲亢", "痛风", "尿酸高", "肥胖"], "system": "内分泌代谢系统", "disease": "糖尿病/代谢异常", "primary": "内分泌代谢疾病", "secondary": "慢病代谢类", "dept": "内分泌代谢科", "score": 0.64},
]

DISEASE_DIRECT_RULES = [
    {"name": "普通上呼吸道感染", "aliases": ["普通感冒", "感冒", "鼻塞", "流鼻涕", "咽痛", "嗓子疼", "喉咙痛"], "primary": "呼吸系统疾病", "secondary": "呼吸系统普通病", "dept": "呼吸内科", "score": 0.68},
    {"name": "支气管炎/肺部感染", "aliases": ["支气管炎", "肺炎", "咳嗽", "咳痰", "发热"], "primary": "呼吸系统疾病", "secondary": "呼吸系统感染", "dept": "呼吸内科", "score": 0.64},
    {"name": "心绞痛/急性冠脉综合征风险", "aliases": ["胸痛", "胸闷", "心梗", "心肌梗死", "冠心病"], "primary": "心血管疾病", "secondary": "心血管急症风险", "dept": "心血管内科", "score": 0.88},
    {"name": "脑卒中风险", "aliases": ["中风", "脑梗", "脑出血", "偏瘫", "口角歪斜", "说话不清", "站不稳", "走路不稳", "无法站立", "天旋地转"], "primary": "神经系统疾病", "secondary": "神经系统急症风险", "dept": "神经内科", "score": 0.90},
    {"name": "阑尾炎/急腹症外科风险", "aliases": ["阑尾炎", "右下腹痛", "右下腹部痛", "右下部腹痛", "右下腹", "右下部", "麦氏点", "反跳痛", "腹肌紧张"], "primary": "外科急腹症", "secondary": "右下腹疼痛类", "dept": "普外科", "score": 0.86},
    {"name": "急性胃肠炎", "aliases": ["腹泻", "呕吐", "肠炎", "胃肠炎"], "primary": "消化系统疾病", "secondary": "消化系统感染类", "dept": "消化内科", "score": 0.62},
    {"name": "皮炎湿疹/过敏反应", "aliases": ["皮疹", "湿疹", "过敏", "皮肤瘙痒"], "primary": "皮肤免疫疾病", "secondary": "皮肤普通病", "dept": "皮肤科", "score": 0.60},
    {"name": "骨关节疾病/外伤", "aliases": ["骨折", "关节炎", "腰椎间盘突出", "颈椎病", "扭伤"], "primary": "骨科疾病", "secondary": "骨关节疼痛类", "dept": "骨科", "score": 0.66},
    {"name": "肿瘤相关疾病", "aliases": ["肿瘤", "癌", "癌症", "放疗", "化疗", "占位"], "primary": "肿瘤疾病", "secondary": "肿瘤专科病类", "dept": "肿瘤科", "score": 0.84},
]


# 扩展候选疾病规则：让 H-Triage 可视化里能出现更具体的疾病/病类候选，而不仅是科室映射。
DISEASE_DIRECT_RULES.extend([
    {"name": "心血管专科疾病", "aliases": ["心脏病", "心绞痛", "心律失常", "房颤", "早搏", "心衰", "心力衰竭", "心肌炎", "心包炎", "心瓣膜病", "先心病", "高血压"], "primary": "心血管疾病", "secondary": "心血管专科病类", "dept": "心血管内科", "score": 0.78},
    {"name": "呼吸慢病/肺部专科疾病", "aliases": ["慢阻肺", "哮喘", "支气管扩张", "慢性支气管炎", "肺结节", "肺部结节", "肺气肿", "胸膜炎", "间质性肺炎"], "primary": "呼吸系统疾病", "secondary": "呼吸专科病类", "dept": "呼吸内科", "score": 0.74},
    {"name": "神经系统专科疾病", "aliases": ["癫痫", "帕金森", "偏头痛", "眩晕症", "面瘫", "阿尔茨海默", "老年痴呆", "三叉神经痛", "周围神经病"], "primary": "神经系统疾病", "secondary": "神经专科病类", "dept": "神经内科", "score": 0.76},
    {"name": "内分泌代谢慢病", "aliases": ["糖尿病", "甲亢", "甲减", "甲状腺结节", "痛风", "高尿酸", "高脂血症", "血脂高", "肥胖症", "骨质疏松"], "primary": "内分泌代谢疾病", "secondary": "慢病代谢类", "dept": "内分泌代谢科", "score": 0.72},
    {"name": "肾脏/泌尿系统疾病", "aliases": ["慢性肾病", "肾炎", "肾衰", "尿毒症", "肾结石", "尿路感染", "膀胱炎", "前列腺炎", "前列腺增生"], "primary": "肾脏泌尿疾病", "secondary": "肾泌尿专科病类", "dept": "肾内科", "score": 0.72},
    {"name": "消化肝胆胰疾病", "aliases": ["胃食管反流", "反流性食管炎", "胃溃疡", "胆囊炎", "胆结石", "胰腺炎", "肝炎", "乙肝", "丙肝", "肝硬化", "脂肪肝", "肠梗阻"], "primary": "消化系统疾病", "secondary": "消化肝胆专科病类", "dept": "消化内科", "score": 0.72},
    {"name": "妇产乳腺疾病", "aliases": ["阴道炎", "盆腔炎", "子宫肌瘤", "卵巢囊肿", "宫颈炎", "多囊卵巢", "乳腺增生", "乳腺结节", "乳腺炎"], "primary": "妇产乳腺疾病", "secondary": "妇产乳腺专科病类", "dept": "妇科", "score": 0.70},
    {"name": "儿科常见专科疾病", "aliases": ["小儿肺炎", "儿童肺炎", "小儿腹泻", "手足口病", "川崎病", "小儿哮喘", "新生儿黄疸", "小儿惊厥"], "primary": "儿科疾病", "secondary": "儿童专科病类", "dept": "儿科", "score": 0.74},
    {"name": "皮肤免疫疾病", "aliases": ["湿疹", "皮炎", "荨麻疹", "银屑病", "牛皮癣", "痤疮", "带状疱疹", "足癣", "灰指甲"], "primary": "皮肤免疫疾病", "secondary": "皮肤专科病类", "dept": "皮肤科", "score": 0.66},
    {"name": "骨关节运动系统疾病", "aliases": ["骨折", "颈椎病", "腰椎间盘突出", "肩周炎", "腱鞘炎", "滑膜炎", "半月板损伤", "韧带损伤", "骨关节炎"], "primary": "骨科疾病", "secondary": "骨关节专科病类", "dept": "骨科", "score": 0.68},
    {"name": "眼耳鼻喉口腔疾病", "aliases": ["鼻炎", "鼻窦炎", "中耳炎", "耳石症", "白内障", "青光眼", "干眼症", "结膜炎", "牙周炎", "龋齿", "智齿"], "primary": "五官口腔疾病", "secondary": "眼耳鼻喉口腔专科病类", "dept": "耳鼻咽喉科", "score": 0.64},
    {"name": "肿瘤/血液专科疾病", "aliases": ["肺癌", "胃癌", "肝癌", "乳腺癌", "肠癌", "结直肠癌", "甲状腺癌", "淋巴瘤", "白血病", "鼻咽癌", "胰腺癌", "宫颈癌", "卵巢癌", "前列腺癌"], "primary": "肿瘤血液疾病", "secondary": "肿瘤血液专科病类", "dept": "肿瘤科", "score": 0.84},
])



def extract_standard_symptom_tags(condition):
    text = condition or ""
    tags = []
    seen = set()
    model_tags, _ = _model_standard_symptom_tags(text)
    for item in model_tags:
        code = item.get("standard_code") or item.get("tag")
        if code and code not in seen:
            seen.add(code)
            tags.append(item)
    for rule in STANDARD_SYMPTOM_RULES:
        hits = [alias for alias in rule["aliases"] if _contains_positive(text, [alias])]
        if hits and rule["tag"] not in seen:
            seen.add(rule["tag"])
            tags.append({
                "tag": rule["tag"],
                "matched_terms": hits[:5],
                "body_system": rule["system"],
                "red_flag_related": bool(rule.get("red")),
            })
    return tags


def _model_disease_meta(disease):
    text = disease or ""
    if any(k in text for k in ("感冒", "肺炎", "哮喘", "结核")):
        dept = "呼吸与危重症医学科" if any(k in text for k in ("肺炎", "哮喘", "结核", "呼吸困难", "低氧")) else "呼吸内科"
        return {"primary": "呼吸系统疾病", "secondary": "模型预测疾病", "dept": dept}
    if any(k in text for k in ("阑尾", "右下腹", "右下部", "反跳痛", "腹肌紧张")):
        return {"primary": "外科急腹症", "secondary": "模型预测疾病", "dept": "普外科"}
    if any(k in text for k in ("胃", "肠", "溃疡", "反流", "肝炎", "黄疸", "胆汁")):
        dept = "感染性疾病科" if any(k in text for k in ("肝炎", "黄疸")) else "消化内科"
        return {"primary": "消化/感染相关疾病", "secondary": "模型预测疾病", "dept": dept}
    if any(k in text for k in ("头痛", "头晕", "眩晕", "头昏", "站不稳", "无法站立", "瘫痪")):
        return {"primary": "神经系统疾病", "secondary": "模型预测疾病", "dept": "神经内科"}
    if any(k in text for k in ("高血压", "心肌梗死")):
        return {"primary": "心血管疾病", "secondary": "模型预测疾病", "dept": "心血管内科"}
    if any(k in text for k in ("糖尿病", "甲状腺", "低血糖")):
        return {"primary": "内分泌代谢疾病", "secondary": "模型预测疾病", "dept": "内分泌代谢科"}
    if any(k in text for k in ("关节", "颈椎")):
        return {"primary": "骨科疾病", "secondary": "模型预测疾病", "dept": "骨科"}
    if any(k in text for k in ("皮", "痤疮", "脓疱", "银屑", "过敏", "真菌")):
        return {"primary": "皮肤免疫疾病", "secondary": "模型预测疾病", "dept": "皮肤科"}
    if any(k in text for k in ("尿路", "尿")):
        return {"primary": "泌尿系统疾病", "secondary": "模型预测疾病", "dept": "泌尿外科"}
    if any(k in text for k in ("艾滋", "疟疾", "登革", "伤寒", "水痘")):
        return {"primary": "感染性疾病", "secondary": "模型预测疾病", "dept": "感染性疾病科"}
    return {"primary": "模型预测疾病", "secondary": "待门诊评估", "dept": "全科医学科"}


def build_htriage_analysis(condition):
    raw_text = condition or ""
    text, colloquial_replacements = normalize_patient_expression(raw_text)
    symptom_tags = extract_standard_symptom_tags(text)
    model_tags, model_prediction = _model_standard_symptom_tags(text)
    seen_tag_names = {item.get("tag") for item in symptom_tags}
    for item in model_tags:
        if item.get("tag") not in seen_tag_names:
            symptom_tags.append(item)
            seen_tag_names.add(item.get("tag"))
    known_disease = detect_known_disease(text)
    disease_scores = {}
    disease_meta = {}

    def add_disease(name, score, rule):
        if not name:
            return
        disease_scores[name] = disease_scores.get(name, 0.0) + score
        disease_meta[name] = {
            "primary": rule["primary"],
            "secondary": rule["secondary"],
            "department": rule["dept"],
        }

    for rule in STANDARD_SYMPTOM_RULES:
        hit_count = sum(1 for alias in rule["aliases"] if _contains_positive(text, [alias]))
        if hit_count:
            add_disease(rule["disease"], rule["score"] + min(0.18, hit_count * 0.04), rule)

    for rule in DISEASE_DIRECT_RULES:
        hit_count = sum(1 for alias in rule["aliases"] if _contains_positive(text, [alias]))
        if hit_count:
            add_disease(rule["name"], rule["score"] + min(0.16, hit_count * 0.04), rule)

    for item in model_prediction.get("predictions", [])[:3]:
        disease = item.get("disease")
        probability = float(item.get("probability") or 0)
        if disease:
            meta = _model_disease_meta(disease)
            score = 0.54 + min(0.38, probability * 1.9)
            add_disease(disease, score, meta)

    if known_disease.get("has_known_disease"):
        add_disease(
            known_disease.get("disease"),
            1.08 if known_disease.get("source") == "user_stated" else 0.90,
            {
                "primary": "用户已知疾病",
                "secondary": "确诊/疑似疾病优先",
                "dept": known_disease.get("department") or "全科医学科",
            },
        )

    if not disease_scores and text:
        matched_dept = None
        for key, dept in DISEASE_DEPT_MAP.items():
            if key in text:
                matched_dept = dept
                add_disease(key, 0.46, {"primary": "未细分病类", "secondary": "待门诊评估", "dept": dept})
                break
        if not matched_dept:
            add_disease("待进一步门诊评估", 0.38, {"primary": "未细分病类", "secondary": "信息不足", "dept": "全科医学科"})

    ranked = sorted(disease_scores.items(), key=lambda item: item[1], reverse=True)[:3]
    max_score = max([score for _, score in ranked], default=1.0)
    disease_candidates = []
    category_scores = {}
    dept_scores = {}
    for name, score in ranked:
        meta = disease_meta.get(name, {})
        probability = int(round(max(8, min(92, (score / max_score) * 82))))
        primary = meta.get("primary", "未细分病类")
        secondary = meta.get("secondary", "待门诊评估")
        dept = meta.get("department", "全科医学科")
        disease_candidates.append({
            "name": name,
            "probability": probability,
            "primary_category": primary,
            "secondary_category": secondary,
            "recommended_department": dept,
            "source": "symptom_disease_model" if secondary == "模型预测疾病" else "rule_engine",
        })
        category_key = f"{primary}/{secondary}"
        category_scores[category_key] = max(category_scores.get(category_key, 0), probability)
        dept_scores[dept] = max(dept_scores.get(dept, 0), probability)

    disease_categories = [
        {"primary": key.split("/", 1)[0], "secondary": key.split("/", 1)[1], "score": score}
        for key, score in sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
    ]
    department_candidates = [
        {"department": dept, "score": score}
        for dept, score in sorted(dept_scores.items(), key=lambda item: item[1], reverse=True)
    ]
    red_flags = [item["tag"] for item in symptom_tags if item.get("red_flag_related")]
    analysis = {
        "model": RANKING_MODEL_VERSION,
        "notice": HTRIAGE_NOTICE,
        "raw_condition": raw_text,
        "normalized_condition": text,
        "colloquial_replacements": colloquial_replacements,
        "known_disease": known_disease,
        "symptom_tags": symptom_tags,
        "disease_candidates": disease_candidates,
        "disease_categories": disease_categories,
        "department_candidates": department_candidates,
        "model_standard_symptoms": [item for item in symptom_tags if item.get("source") == "symptom_disease_model"],
        "model_disease_prediction": model_prediction,
        "red_flag_tags": red_flags,
    }
    analysis["followup"] = build_followup_questions(text, analysis)
    return analysis


def _attach_htriage_fields(payload, analysis):
    payload["normalized_condition"] = analysis.get("normalized_condition", "")
    payload["colloquial_replacements"] = analysis.get("colloquial_replacements", [])
    payload["known_disease"] = analysis.get("known_disease", {})
    payload["symptom_tags"] = analysis.get("symptom_tags", [])
    payload["disease_candidates"] = analysis.get("disease_candidates", [])
    payload["disease_categories"] = analysis.get("disease_categories", [])
    payload["department_candidates"] = analysis.get("department_candidates", [])
    payload["model_standard_symptoms"] = analysis.get("model_standard_symptoms", [])
    payload["model_disease_prediction"] = analysis.get("model_disease_prediction", {})
    payload["followup"] = analysis.get("followup", {})
    payload["disease_prediction_notice"] = analysis.get("notice", HTRIAGE_NOTICE)
    payload["htriage_model"] = analysis.get("model", RANKING_MODEL_VERSION)
    if analysis.get("red_flag_tags"):
        payload["red_flag_tags"] = analysis.get("red_flag_tags")
    return payload


def _htriage_public_payload(triage):
    triage = triage or {}
    return {
        "model": triage.get("htriage_model", RANKING_MODEL_VERSION),
        "notice": triage.get("disease_prediction_notice", HTRIAGE_NOTICE),
        "normalized_condition": triage.get("normalized_condition", ""),
        "colloquial_replacements": triage.get("colloquial_replacements", []),
        "known_disease": triage.get("known_disease", {}),
        "symptom_tags": triage.get("symptom_tags", []),
        "model_standard_symptoms": triage.get("model_standard_symptoms", []),
        "disease_candidates": triage.get("disease_candidates", []),
        "disease_categories": triage.get("disease_categories", []),
        "department_candidates": triage.get("department_candidates", []),
        "model_disease_prediction": triage.get("model_disease_prediction", {}),
        "followup": triage.get("followup", {}),
        "red_flag_tags": triage.get("red_flag_tags", []),
    }


def analyze_medical_triage(condition, scenario="common"):
    """返回可解释的病情轻重判定，不替代医生诊断。"""
    text = (condition or "").strip()
    htriage = build_htriage_analysis(text)
    matched_dept = match_department(text)
    if htriage.get("department_candidates"):
        matched_dept = htriage["department_candidates"][0]["department"]

    critical_hits = [w for w in TRIAGE_CRITICAL_SINGLE_KEYWORDS if _contains_positive(text, [w])]
    if critical_hits:
        return _attach_htriage_fields({
            "level": "emergency",
            "label": "疑似急症",
            "severity_bucket": "大病/重症风险",
            "severity_score": 96,
            "care_level": "建议立即急诊/急救评估",
            "recommended_scenario": "surgery",
            "matched_rule": "命中危急强信号",
            "matched_department": matched_dept or "急诊医学科",
            "reasons": ["命中危急症状信号：" + "、".join(critical_hits[:4]) + "。请优先拨打 120 或前往就近急诊。"],
            "disclaimer": "本系统仅做分诊辅助；如症状明显、持续加重或出现意识/呼吸/胸痛等风险，请及时拨打 120 或前往急诊。",
        }, htriage)

    for rule in TRIAGE_RED_FLAGS:
        hit_main = _contains_positive(text, rule["keywords"])
        hit_context = (
            not rule["with_any"] or
            _contains_positive(text, rule["with_any"]) or
            (hit_main and _contains_positive(text, TRIAGE_SEVERE_MODIFIERS))
        )
        if hit_main and hit_context:
            rule_dept = rule["dept"]
            triage_dept = matched_dept if matched_dept and matched_dept != "急诊医学科" else rule_dept
            return _attach_htriage_fields({
                "level": "emergency",
                "label": "疑似急症",
                "severity_bucket": "大病/重症风险",
                "severity_score": 95,
                "care_level": "建议优先急诊/急救评估",
                "recommended_scenario": "surgery",
                "matched_rule": rule["name"],
                "matched_department": triage_dept,
                "reasons": [rule["advice"]],
                "disclaimer": "本系统仅做分诊辅助；如症状明显、持续加重或出现意识/呼吸/胸痛等风险，请及时拨打 120 或前往急诊。",
            }, htriage)

    urgent_hits = [w for w in TRIAGE_URGENT_KEYWORDS if _contains_positive(text, [w])]
    mild_hits = [w for w in TRIAGE_MILD_KEYWORDS if w in text]
    specialty_rule = None
    specialty_hits = []
    for rule in TRIAGE_SPECIALTY_DISEASE_RULES:
        hits = [w for w in rule["keywords"] if _contains_positive(text, [w])]
        if hits:
            specialty_rule = rule
            specialty_hits = hits
            break

    if specialty_rule:
        return _attach_htriage_fields({
            "level": "urgent",
            "label": "专科病情/需评估",
            "severity_bucket": "专科病情/需评估",
            "severity_score": 64,
            "care_level": "建议尽快到对应专科门诊评估",
            "recommended_scenario": "complex",
            "matched_rule": specialty_rule["name"],
            "matched_department": matched_dept or specialty_rule["dept"],
            "reasons": [specialty_rule["advice"], "如伴随胸痛、呼吸困难、大汗、晕厥等表现，请优先急诊或拨打 120。"],
            "disclaimer": "本系统仅做分诊辅助；明确慢病或专科病名不等于急症，但需要按专科规范评估。",
        }, htriage)

    if urgent_hits or scenario in ("surgery", "complex"):
        return _attach_htriage_fields({
            "level": "urgent",
            "label": "较重/需尽快就医",
            "severity_bucket": "较重病情",
            "severity_score": 72,
            "care_level": "建议当天或尽快到医院就诊",
            "recommended_scenario": "complex" if scenario != "surgery" else "surgery",
            "matched_rule": "症状较重或存在风险关键词",
            "matched_department": matched_dept,
            "reasons": ["命中较重症状关键词：" + "、".join(urgent_hits[:4]) if urgent_hits else "当前场景更适合优先匹配专科能力强的医生。"],
            "disclaimer": "若出现胸痛、呼吸困难、意识异常、肢体无力等急症表现，请优先急诊。",
        }, htriage)

    if mild_hits or scenario == "common":
        return _attach_htriage_fields({
            "level": "routine",
            "label": "普通/常见病倾向",
            "severity_bucket": "小病/常见病倾向",
            "severity_score": 35,
            "care_level": "可优先选择门诊或社区首诊",
            "recommended_scenario": "common",
            "matched_rule": "普通症状或常见病描述",
            "matched_department": matched_dept,
            "reasons": ["更适合按科室匹配、距离和可及门诊资源综合推荐。"],
            "disclaimer": "若症状持续加重、超过数日不缓解，或出现急症表现，请及时线下就医。",
        }, htriage)

    return _attach_htriage_fields({
        "level": "routine",
        "label": "待进一步判断",
        "severity_bucket": "信息不足",
        "severity_score": 50,
        "care_level": "建议门诊评估，必要时完善检查",
        "recommended_scenario": "first_visit" if scenario == "first_visit" else "common",
        "matched_rule": "未命中明确急症红旗",
        "matched_department": matched_dept,
        "reasons": ["描述信息有限，先按匹配科室、距离和医生画像综合推荐。"],
        "disclaimer": "本系统不提供诊断结论，仅辅助选择就诊方向。",
    }, htriage)

# 用户位置（模拟）
USER_LOCATIONS = {
    "天宁区": (31.7760, 119.9600),
    "钟楼区": (31.7850, 119.9450),
    "武进区": (31.7300, 119.9500),
    "新北区": (31.8200, 119.9700),
    "金坛区": (31.7200, 119.5800),
    "溧阳市": (31.4100, 119.4800),
}


# ============================================================
# 工具函数
# ============================================================

def haversine(lat1, lng1, lat2, lng2):
    """计算两个GPS坐标之间的距离（公里）"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def match_department(condition):
    """根据病情匹配对应科室"""
    condition = condition.strip()
    if condition in DISEASE_DEPT_MAP:
        return DISEASE_DEPT_MAP[condition]

    matched = []
    for index, (key, dept) in enumerate(DISEASE_DEPT_MAP.items()):
        if key in condition and _contains_positive(condition, [key]):
            matched.append((len(key), -index, dept))
        elif condition in key:
            matched.append((len(condition), -index, dept))
    if matched:
        matched.sort(reverse=True)
        return matched[0][2]
    htriage = build_htriage_analysis(condition)
    if htriage.get("department_candidates"):
        return htriage["department_candidates"][0]["department"]
    return None


def recommend(condition, user_lat, user_lng, top_n=5, triage=None):
    """
    多目标医疗推荐排序：
    1. 安全分诊结果先行，急症优先急诊能力和医院质量
    2. 临床匹配、承载可用、距离可及、连续照护、服务质量、公平性共同精排
    3. 对不适合的候选施加风险惩罚，并在 Top-N 中做轻量多样性重排
    """
    target_dept = (triage or {}).get("matched_department") or match_department(condition)
    triage_level = (triage or {}).get("level", "routine")
    weight_key = "first_visit" if (triage or {}).get("recommended_scenario") == "first_visit" else triage_level
    weights = HOSPITAL_RANKING_WEIGHTS.get(weight_key, HOSPITAL_RANKING_WEIGHTS["routine"])

    results = []
    for h in HOSPITALS:
        distance = haversine(user_lat, user_lng, h["lat"], h["lng"])

        access_context = "first_visit" if weight_key == "first_visit" else triage_level
        accessibility = _access_score(h, user_lat, user_lng, access_context)
        traffic_access = _hospital_traffic_access(h)
        traffic_access["used_in_ranking"] = access_context not in ("emergency", "urgent")
        traffic_access["ranking_policy"] = "急症/较重病情不使用公交/出租车权重" if not traffic_access["used_in_ranking"] else "普通/初诊场景使用公交站点和出租车样本辅助可达性测算"
        clinical = _hospital_strength_for_dept(h, target_dept)
        population_fit = _special_population_fit(condition, h)
        clinical = _clamp(clinical * 0.82 + population_fit * 0.18)
        availability = _hospital_availability_score(h, triage_level)
        quality = _hospital_quality_score(h)
        continuity = _continuity_score(condition, target_dept, h)
        fairness = _fairness_score(condition, h, distance, "first_visit" if weight_key == "first_visit" else triage_level)
        emergency = 1.0 if h.get("emergency") else 0.55
        risk_penalty = _hospital_risk_penalty(condition, target_dept, h, triage or {})

        matched_dept = target_dept
        if target_dept and target_dept in h.get("strength_scores", {}):
            strength_score = h["strength_scores"][target_dept]
        elif target_dept and target_dept in h.get("departments", []):
            strength_score = 75  # 有该科室但非强项
        else:
            strength_score = 50
            for d in h.get("departments", []):
                if target_dept and _departments_related(target_dept, d):
                    strength_score = 70
                    matched_dept = d
                    break

        raw_score = (
            weights["clinical"] * clinical +
            weights["availability"] * availability +
            weights["accessibility"] * accessibility +
            weights["continuity"] * continuity +
            weights["quality"] * quality +
            weights["fairness"] * fairness +
            weights["emergency"] * emergency -
            risk_penalty
        )
        composite = round(_clamp(raw_score) * 100, 1)
        feature_scores = {
            "clinical": round(clinical, 4),
            "availability": round(availability, 4),
            "accessibility": round(accessibility, 4),
            "continuity": round(continuity, 4),
            "quality": round(quality, 4),
            "fairness": round(fairness, 4),
            "emergency": round(emergency, 4),
            "risk_penalty": round(risk_penalty, 4),
            "traffic_access": traffic_access,
        }

        results.append({
            "hospital": h,
            "distance": distance,
            "dist_score": round(accessibility * 100, 1),
            "strength_score": strength_score,
            "composite_score": composite,
            "matched_department": matched_dept or target_dept,
            "feature_scores": feature_scores,
            "traffic_access": traffic_access,
            "ranking_weights": weights,
            "ranking_model": RANKING_MODEL_VERSION,
            "explanations": _hospital_recommend_reasons(h, feature_scores, distance, matched_dept or target_dept, triage_level),
        })

    results.sort(key=lambda x: x["composite_score"], reverse=True)
    selected = []
    district_count = {}
    tertiary_count = 0
    for item in results:
        h = item["hospital"]
        adjusted = item["composite_score"]
        district = _hospital_district(h)
        if triage_level in ("routine", "urgent") and district_count.get(district, 0) >= 2:
            adjusted -= 1.5
        if triage_level == "routine" and h.get("level") == "三级甲等" and tertiary_count >= 2:
            adjusted -= 2.0
        item["rerank_adjustment"] = round(adjusted - item["composite_score"], 1)
        item["composite_score"] = round(_clamp(adjusted / 100.0) * 100, 1)
        selected.append(item)
        district_count[district] = district_count.get(district, 0) + 1
        if h.get("level") == "三级甲等":
            tertiary_count += 1
        if len(selected) >= top_n:
            break
    selected.sort(key=lambda x: x["composite_score"], reverse=True)
    return selected


def recommend_doctors(condition, top_n=5):
    """根据病情推荐最合适的医生"""
    target_dept = match_department(condition)
    if not target_dept:
        return []

    candidates = []
    for d in DOCTORS:
        if d["department"] == target_dept or target_dept in d["department"]:
            score = 95
            candidates.append({"doctor": d, "score": round(score, 1)})
        elif any(target_dept in s or s in target_dept for s in d["specialties"]):
            score = 85
            candidates.append({"doctor": d, "score": round(score, 1)})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_n]


# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# API 路由（后期对接真实数据库的接口预留位置）
# ============================================================

@app.route("/api/hospitals")
def api_hospitals():
    """获取所有医院列表 [接口预留: 对接医院信息数据库]"""
    return jsonify({"code": 200, "data": HOSPITALS, "count": len(HOSPITALS)})


@app.route("/api/hospitals/<int:hid>")
def api_hospital_detail(hid):
    """获取单个医院详情 [已接入多院区真实数据]"""
    h = next((x for x in HOSPITALS if x["id"] == hid), None)
    if h:
        doctors = [d for d in REAL_DOCTORS if d["hospital_id"] == hid]
        if not doctors:
            doctors = [d for d in DOCTORS if d["hospital_id"] == hid]
        data_source = "real" if any(d["hospital_id"] == hid for d in REAL_DOCTORS) else "mock"
        return jsonify({"code": 200, "data": {"hospital": h, "doctors": doctors, "source": data_source}})
    return jsonify({"code": 404, "message": "医院不存在"}), 404


@app.route("/api/doctors")
def api_doctors():
    """获取医生列表 [已接入真实爬取数据]"""
    dept = request.args.get("department")
    hid = request.args.get("hospital_id", type=int)
    use_real = request.args.get("real", "1")  # 默认返回真实数据

    # 合并真实数据和模拟数据
    result = REAL_DOCTORS if use_real == "1" else DOCTORS
    if not result:
        result = DOCTORS

    if dept:
        result = [d for d in result if d["department"] == dept]
    if hid:
        result = [d for d in result if d["hospital_id"] == hid]
    return jsonify({"code": 200, "data": result, "count": len(result), "source": "real" if use_real == "1" else "mock"})


@app.route("/api/doctors/<int:did>")
def api_doctor_detail(did):
    """获取单个医生详情 [接口预留: 对接医生信息数据库]"""
    d = next((x for x in DOCTORS if x["id"] == did), None)
    if d:
        hospital = next((h for h in HOSPITALS if h["id"] == d["hospital_id"]), None)
        return jsonify({"code": 200, "data": {"doctor": d, "hospital": hospital}})
    return jsonify({"code": 404, "message": "医生不存在"}), 404


@app.route("/api/predict-disease", methods=["POST"])
def api_predict_disease():
    """根据症状预测中文疾病名称。"""
    data = request.get_json() or {}
    symptoms = data.get("symptoms")
    condition = data.get("condition")
    details = bool(data.get("details"))
    symptom_input = symptoms if symptoms else condition

    if not symptom_input:
        return jsonify({"code": 400, "message": "请输入症状"}), 400

    prediction = predict_disease_name(symptom_input, details=details)
    if not prediction.get("available", True):
        return jsonify({
            "code": 503,
            "message": "疾病预测模型不可用",
            "data": prediction,
        }), 503

    disease = prediction.get("disease", "")
    if not disease:
        return jsonify({"code": 400, "message": "症状信息不足", "data": prediction}), 400
    if details:
        prediction["standard_symptom_tags"], _ = _model_standard_symptom_tags(symptom_input)

    return jsonify({
        "code": 200,
        "disease": disease,
        "data": prediction if details else {"disease": disease},
    })


@app.route("/api/triage", methods=["POST"])
def api_triage():
    """病情轻重辅助判定接口，不替代医生诊断。"""
    data = request.get_json() or {}
    condition = data.get("condition", "")
    scenario = data.get("scenario", "common")
    if not condition:
        return jsonify({"code": 400, "message": "请输入病情或症状"}), 400
    triage = analyze_medical_triage(condition, scenario)
    return jsonify({
        "code": 200,
        "data": {
            "condition": condition,
            "matched_department": triage.get("matched_department") or match_department(condition),
            "disease_prediction": predict_disease_name(condition, details=True),
            "triage": triage,
            "htriage_analysis": _htriage_public_payload(triage),
        }
    })


@app.route("/api/followup", methods=["POST"])
def api_followup():
    """根据当前描述生成补充追问建议，不做最终诊断。"""
    data = request.get_json() or {}
    condition = data.get("condition", "")
    scenario = data.get("scenario", "common")
    if not condition:
        return jsonify({"code": 400, "message": "请输入病情或症状"}), 400
    triage = analyze_medical_triage(condition, scenario)
    return jsonify({
        "code": 200,
        "data": {
            "condition": condition,
            "matched_department": triage.get("matched_department") or match_department(condition),
            "triage_level": triage.get("level"),
            "triage_label": triage.get("label"),
            "htriage_analysis": _htriage_public_payload(triage),
            "followup": triage.get("followup", {}),
            "known_disease": triage.get("known_disease", {}),
        }
    })


def _trim_feedback_value(value, max_len=1200):
    if isinstance(value, str):
        return value[:max_len]
    if isinstance(value, list):
        return [_trim_feedback_value(v, max_len=max_len) for v in value[:20]]
    if isinstance(value, dict):
        return {str(k)[:80]: _trim_feedback_value(v, max_len=max_len) for k, v in list(value.items())[:40]}
    return value


def _append_test_feedback(kind, payload):
    os.makedirs(os.path.dirname(TEST_FEEDBACK_PATH), exist_ok=True)
    item = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kind": kind,
        "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip(),
        "user_agent": (request.headers.get("User-Agent") or "")[:240],
        "payload": _trim_feedback_value(payload or {}),
    }
    with open(TEST_FEEDBACK_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


@app.route("/api/test-feedback", methods=["POST"])
def api_test_feedback():
    """接收外部测试者手动反馈，保存到本机 data/test_feedback.jsonl。"""
    data = request.get_json() or {}
    feedback = (data.get("feedback") or "").strip()
    if not feedback:
        return jsonify({"code": 400, "message": "请填写反馈内容"}), 400
    item = _append_test_feedback("manual_feedback", data)
    return jsonify({
        "code": 200,
        "message": "反馈已保存到主机",
        "data": {"time": item["time"], "saved": True},
    })


@app.route("/api/test-record", methods=["POST"])
def api_test_record():
    """接收测试者推荐流程摘要，便于赛前测试复盘。"""
    data = request.get_json() or {}
    item = _append_test_feedback("recommend_record", data)
    return jsonify({
        "code": 200,
        "message": "测试记录已保存",
        "data": {"time": item["time"], "saved": True},
    })


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    """
    智能推荐接口 [已接入真实数据 + 动态权重]
    请求参数: { condition, scenario: surgery|common|complex|first_visit, district, lat?, lng? }
    """
    data = request.get_json() or {}
    condition = data.get("condition", "")
    scenario = data.get("scenario", "common")
    district = data.get("district", "天宁区")
    expert_preference = data.get("expert_preference", "system")
    lat = data.get("lat")
    lng = data.get("lng")

    if not condition:
        return jsonify({"code": 400, "message": "请输入病情或症状"}), 400

    if lat is None or lng is None:
        if district in USER_LOCATIONS:
            lat, lng = USER_LOCATIONS[district]
        else:
            lat, lng = 31.7760, 119.9600

    triage = analyze_medical_triage(condition, scenario)
    effective_scenario = triage.get("recommended_scenario") or scenario
    resource_strategy = _resource_strategy(triage, expert_preference)

    hospitals = recommend(condition, lat, lng, triage=triage)
    # 优先使用真实医生数据 + 动态权重
    doctors = enhanced_recommend_doctors(
        condition,
        effective_scenario,
        top_n=8,
        user_lat=lat,
        user_lng=lng,
        triage=triage,
        expert_preference=expert_preference
    ) if REAL_DOCTORS else recommend_doctors(condition)

    matched_dept = triage.get("matched_department") or match_department(condition)

    return jsonify({
        "code": 200,
        "data": {
            "condition": condition,
            "scenario": scenario,
            "effective_scenario": effective_scenario,
            "expert_preference": expert_preference,
            "resource_strategy": resource_strategy,
            "triage": triage,
            "htriage_analysis": _htriage_public_payload(triage),
            "disease_prediction": predict_disease_name(condition, details=True),
            "matched_department": matched_dept,
            "user_location": {"district": district, "lat": lat, "lng": lng},
            "recommended_hospitals": hospitals,
            "recommended_doctors": doctors,
            "weights_used": ENHANCED_WEIGHTS.get(effective_scenario, ENHANCED_WEIGHTS["surgery"]),
            "hospital_weights_used": HOSPITAL_RANKING_WEIGHTS.get(triage.get("level", "routine"), HOSPITAL_RANKING_WEIGHTS["routine"]),
            "ranking_model": RANKING_MODEL_VERSION,
            "data_source": "real" if REAL_DOCTORS else "mock",
            "total_real_doctors": len(REAL_DOCTORS),
        }
    })


@app.route("/api/hospitals/<int:hid>/doctors")
def api_hospital_doctors(hid):
    """获取某医院的所有医生 [真实数据]"""
    result = [d for d in REAL_DOCTORS if d["hospital_id"] == hid]
    if not result:
        result = [d for d in DOCTORS if d["hospital_id"] == hid]
    hospital = next((h for h in HOSPITALS if h["id"] == hid), None)
    return jsonify({
        "code": 200,
        "data": {
            "hospital": hospital,
            "doctors": result,
            "count": len(result),
            "source": "real" if any(d["id"] >= 1000 for d in result) else "mock"
        }
    })


@app.route("/api/departments")
def api_departments():
    """获取科室列表"""
    depts = set()
    for h in HOSPITALS:
        for d in h["departments"]:
            depts.add(d)
    return jsonify({"code": 200, "data": sorted(depts)})


@app.route("/api/districts")
def api_districts():
    """获取区域列表"""
    return jsonify({"code": 200, "data": list(USER_LOCATIONS.keys())})


@app.route("/api/recommend/enhanced", methods=["POST"])
def api_enhanced_recommend():
    """
    增强版推荐接口 [已接入爬取的真实医生数据 + 动态权重]
    请求参数: { condition, scenario: surgery|common|complex|first_visit, district }
    """
    data = request.get_json() or {}
    condition = data.get("condition", "")
    scenario = data.get("scenario", "common")
    district = data.get("district", "天宁区")
    expert_preference = data.get("expert_preference", "system")
    lat = data.get("lat")
    lng = data.get("lng")

    if not condition:
        return jsonify({"code": 400, "message": "请输入病情或症状"}), 400

    if lat is None or lng is None:
        if district in USER_LOCATIONS:
            lat, lng = USER_LOCATIONS[district]
        else:
            lat, lng = 31.7760, 119.9600

    triage = analyze_medical_triage(condition, scenario)
    effective_scenario = triage.get("recommended_scenario") or scenario
    resource_strategy = _resource_strategy(triage, expert_preference)

    # 医院推荐
    hospitals = recommend(condition, lat, lng, triage=triage)
    # 增强医生推荐 (使用真实数据)
    doctors = enhanced_recommend_doctors(
        condition,
        effective_scenario,
        user_lat=lat,
        user_lng=lng,
        triage=triage,
        expert_preference=expert_preference
    )

    matched_dept = triage.get("matched_department") or match_department(condition)

    return jsonify({
        "code": 200,
        "data": {
            "condition": condition,
            "scenario": scenario,
            "effective_scenario": effective_scenario,
            "expert_preference": expert_preference,
            "resource_strategy": resource_strategy,
            "triage": triage,
            "htriage_analysis": _htriage_public_payload(triage),
            "disease_prediction": predict_disease_name(condition, details=True),
            "matched_department": matched_dept,
            "user_location": {"district": district, "lat": lat, "lng": lng},
            "recommended_hospitals": hospitals,
            "recommended_doctors": doctors,
            "weights_used": ENHANCED_WEIGHTS.get(effective_scenario, ENHANCED_WEIGHTS["surgery"]),
            "hospital_weights_used": HOSPITAL_RANKING_WEIGHTS.get(triage.get("level", "routine"), HOSPITAL_RANKING_WEIGHTS["routine"]),
            "ranking_model": RANKING_MODEL_VERSION,
            "data_source": "real_data",  # 标明数据来自爬取
        }
    })


@app.route("/api/recommend/rerank", methods=["POST"])
def api_rerank_by_distance():
    """
    距离重排接口：用户优推医生后，按距离从近到远重新排序
    请求参数: { doctor_ids: [int, ...], district: str, lat?: float, lng?: float }
    """
    data = request.get_json() or {}
    doctor_ids = data.get("doctor_ids", [])
    district = data.get("district", "天宁区")
    lat = data.get("lat")
    lng = data.get("lng")

    if not doctor_ids:
        return jsonify({"code": 400, "message": "请提供需要重排的医生ID列表"}), 400

    if lat is not None and lng is not None:
        user_lat, user_lng = float(lat), float(lng)
    else:
        if district not in USER_LOCATIONS:
            district = "天宁区"
        user_lat, user_lng = USER_LOCATIONS[district]

    results = []
    for did in doctor_ids:
        doc = None
        for d in REAL_DOCTORS:
            if d["id"] == did:
                doc = d
                break
        if not doc:
            for d in DOCTORS:
                if d["id"] == did:
                    doc = d
                    break
        if not doc:
            continue

        hid = doc["hospital_id"]
        hospital = next((h for h in HOSPITALS if h["id"] == hid), None)
        if not hospital:
            continue

        distance = haversine(user_lat, user_lng, hospital["lat"], hospital["lng"])
        results.append({
            "doctor": doc,
            "hospital": {
                "id": hospital["id"],
                "name": hospital["name"],
                "level": hospital["level"],
                "address": hospital["address"],
                "lat": hospital["lat"],
                "lng": hospital["lng"],
            },
            "distance_km": distance,
        })

    results.sort(key=lambda r: r["distance_km"])

    return jsonify({
        "code": 200,
        "data": {
            "user_district": district,
            "user_location": {"lat": user_lat, "lng": user_lng},
            "ranked_doctors": results,
            "count": len(results),
        }
    })


@app.route("/api/doctors/detail/<int:did>")
def api_doctor_detail_enhanced(did):
    """获取医生详细信息 [真实数据, 含手术量/论文/科研成果]"""
    # 先在真实数据中查找
    for d in REAL_DOCTORS:
        if d["id"] == did:
            return jsonify({"code": 200, "data": d})
    # 再查模拟数据
    d = next((x for x in DOCTORS if x["id"] == did), None)
    if d:
        hospital = next((h for h in HOSPITALS if h["id"] == d["hospital_id"]), None)
        return jsonify({"code": 200, "data": {"doctor": d, "hospital": hospital}})
    return jsonify({"code": 404, "message": "医生不存在"}), 404


@app.route("/api/stats")
def api_stats():
    """系统统计概览 [接口预留: 对接大数据平台]"""
    return jsonify({
        "code": 200,
        "data": {
            "total_hospitals": len(HOSPITALS),
            "total_doctors": len(REAL_DOCTORS) if REAL_DOCTORS else len(DOCTORS),
            "total_real_doctors": len(REAL_DOCTORS),
            "total_mock_doctors": len(DOCTORS),
            "total_beds": sum(h["beds"] for h in HOSPITALS),
            "daily_outpatients_total": sum(h["daily_outpatients"] for h in HOSPITALS),
            "top_departments": ["心血管内科", "骨科", "肿瘤科", "神经内科", "消化内科"],
        }
    })

@app.route("/api/transit/routes")
def api_transit_routes():
    """公共交通线路脱敏数据。"""
    return jsonify({
        "code": 200,
        "data": BUS_ROUTE_DATA.get("routes", []),
        "summary": BUS_ROUTE_DATA.get("summary", {}),
    })

@app.route("/api/transit/stations")
def api_transit_stations():
    """公共交通站点脱敏数据。"""
    return jsonify({
        "code": 200,
        "data": BUS_STATION_DATA.get("stations", []),
        "summary": BUS_STATION_DATA.get("summary", {}),
    })

@app.route("/api/transit/taxi-operations")
def api_transit_taxi_operations():
    """出租车/网约车运营脱敏样本数据。"""
    return jsonify({
        "code": 200,
        "data": TAXI_OPERATION_DATA.get("operations", []),
        "summary": TAXI_OPERATION_DATA.get("summary", {}),
    })

@app.route("/api/transit/bike-stations")
def api_transit_bike_stations():
    """公共自行车/助力车站点脱敏数据。"""
    return jsonify({
        "code": 200,
        "data": BIKE_STATION_DATA.get("stations", []),
        "summary": BIKE_STATION_DATA.get("summary", {}),
    })

@app.route("/api/transit/bike-vehicles")
def api_transit_bike_vehicles():
    """共享单车/助力车车辆状态脱敏数据。"""
    return jsonify({
        "code": 200,
        "data": BIKE_VEHICLE_DATA.get("vehicles", []),
        "summary": BIKE_VEHICLE_DATA.get("summary", {}),
    })

@app.route("/api/transit/stats")
def api_transit_stats():
    """公共交通供给能力统计，用于公共数据融合看板。"""
    return jsonify({
        "code": 200,
        "data": _bus_route_stats(),
    })


@app.route("/api/assistant/process", methods=["POST"])
def api_assistant_process():
    """处理医疗小助手收集的问答，生成优化后的病情描述"""
    data = request.get_json() or {}
    answers = data.get("answers", {})

    if not answers:
        return jsonify({"code": 400, "message": "请提供问诊回答"}), 400

    parts = []
    if answers.get("step0"):
        parts.append(answers["step0"])
    if answers.get("step1"):
        parts.append(f"持续{answers['step1']}")
    if answers.get("step2"):
        severity = answers["step2"]
        if "较严重" in severity:
            parts.insert(0, "严重症状")
        elif "严重" in severity:
            parts.insert(0, "中度症状")
    if answers.get("step3") and answers["step3"] != "没有其他症状":
        parts.append(answers["step3"])

    condition = "；".join(parts) if parts else answers.get("step0", "")
    matched_dept = match_department(answers.get("step0", ""))
    triage = analyze_medical_triage(condition, "first_visit")

    return jsonify({
        "code": 200,
        "data": {
            "condition": condition,
            "matched_department": matched_dept,
            "disease_prediction": predict_disease_name(condition, details=True),
            "triage": triage,
            "htriage_analysis": _htriage_public_payload(triage),
        }
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  常州市智能医疗推荐系统 - 演示版")
    print("  Smart Medical Recommendation System")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=5002)
