# Disease Symptom Training Dataset

This dataset is prepared for prototyping disease-label prediction from symptom tags/text. It is not a clinical decision system and should not be used for diagnosis without medical validation.

## Outputs

- `disease_symptom_training_long.csv`: one row per case, with `disease`, pipe-separated `symptom_tags`, readable `symptom_text`, `num_symptoms`, and `source`.
- `disease_symptom_training_onehot.csv`: one row per case, with `disease` plus one binary column per symptom tag.
- `disease_symptom_structured_41diseases_long.csv`: cleaner structured subset from the MIT-licensed source only.
- `disease_symptom_structured_41diseases_onehot.csv`: compact one-hot matrix for a first baseline model.
- `disease_symptom_sources.json`: source URLs and license notes captured during collection.

## Summary

- Rows: 2,726
- Unique disease labels: 1,095
- Unique symptom tags: 10,596
- One-hot columns: 10,599

## Rows By Source

- fhai50032_symptoms_to_disease_7k: 2,422
- shanover_disease_symptoms_prec_full: 304

## Top Disease Labels

- Dengue: 70
- Diabetes: 69
- Common Cold: 68
- Malaria: 67
- Pneumonia: 66
- Psoriasis: 65
- Typhoid: 65
- Arthritis: 63
- Bronchial Asthma: 63
- Impetigo: 63
- Hypertension: 62
- Migraine: 62
- Allergy: 60
- Chicken Pox: 60
- Drug Reaction: 60
- Varicose Veins: 59
- Cervical Spondylosis: 56
- Jaundice: 55
- Urinary Tract Infection: 54
- Fungal Infection: 53

## Top Symptom Tags

- fatigue: 277
- vomiting: 264
- nausea: 184
- high_fever: 179
- loss_of_appetite: 165
- headache: 160
- chills: 152
- abdominal_pain: 141
- yellowish_skin: 122
- yellowing_of_eyes: 116
- malaise: 106
- chest_pain: 103
- joint_pain: 96
- sweating: 90
- skin_rash: 84
- irritability: 84
- itching: 83
- dark_urine: 82
- cough: 75
- muscle_pain: 71
- excessive_hunger: 71
- diarrhoea: 70
- weight_loss: 65
- lethargy: 64
- mild_fever: 55
- breathlessness: 53
- blurred_and_distorted_vision: 53
- swelled_lymph_nodes: 52
- phlegm: 52
- dizziness: 45

## Source Notes

- shanover_disease_symptoms_prec_full: https://huggingface.co/datasets/shanover/disease_symptoms_prec_full (MIT (per Hugging Face dataset tags))
- fhai50032_symptoms_to_disease_7k: https://huggingface.co/datasets/fhai50032/Symptoms_to_disease_7k (Apache-2.0 (per Hugging Face dataset tags))

## Modeling Notes

- Treat labels as weak/synthetic educational data unless you independently verify provenance and clinical quality.
- Split train/test by disease-stratified sampling where possible; repeated symptom combinations can leak across splits.
- Prefer top-k metrics and calibration checks because many diseases share symptom profiles.
- Add a clear user-facing disclaimer if this powers an app: symptom prediction is not medical advice.
