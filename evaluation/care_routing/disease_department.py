"""Disease-label to department mapping used only for offline evaluation.

Aligned with production `_model_disease_meta` / `DISEASE_DEPT_MAP` semantics
where those rules already decide a department for the same disease text.
This map is evaluation metadata, not a patient-facing routing table.
"""

from __future__ import annotations

# Primary department for each of the 41 prototype model disease labels.
DISEASE_TO_DEPARTMENT: dict[str, str] = {
    "(vertigo) Paroymsal Positional Vertigo": "神经内科",
    "AIDS": "感染性疾病科",
    "Acne": "皮肤科",
    "Alcoholic hepatitis": "消化内科",
    "Allergy": "皮肤科",
    "Arthritis": "骨科",
    "Bronchial Asthma": "呼吸与危重症医学科",
    "Cervical spondylosis": "骨科",
    "Chicken pox": "感染性疾病科",
    "Chronic cholestasis": "消化内科",
    "Common Cold": "呼吸内科",
    "Dengue": "感染性疾病科",
    "Diabetes": "内分泌代谢科",
    "Dimorphic hemmorhoids(piles)": "肛肠科",
    "Drug Reaction": "皮肤科",
    "Fungal infection": "皮肤科",
    "GERD": "消化内科",
    "Gastroenteritis": "消化内科",
    "Heart attack": "心血管内科",
    "Hepatitis B": "感染性疾病科",
    "Hepatitis C": "感染性疾病科",
    "Hepatitis D": "感染性疾病科",
    "Hepatitis E": "感染性疾病科",
    "Hypertension": "心血管内科",
    "Hyperthyroidism": "内分泌代谢科",
    "Hypoglycemia": "内分泌代谢科",
    "Hypothyroidism": "内分泌代谢科",
    "Impetigo": "皮肤科",
    "Jaundice": "消化内科",
    "Malaria": "感染性疾病科",
    "Migraine": "神经内科",
    "Osteoarthristis": "骨科",
    "Paralysis (brain hemorrhage)": "神经内科",
    "Peptic ulcer diseae": "消化内科",
    "Pneumonia": "呼吸与危重症医学科",
    "Psoriasis": "皮肤科",
    "Tuberculosis": "呼吸与危重症医学科",
    "Typhoid": "感染性疾病科",
    "Urinary tract infection": "泌尿外科",
    "Varicose veins": "普外科",
    "hepatitis A": "感染性疾病科",
}


def department_for(disease: str) -> str:
    return DISEASE_TO_DEPARTMENT.get(disease, "全科医学科")


def department_set(diseases: list[str]) -> set[str]:
    return {department_for(name) for name in diseases}
