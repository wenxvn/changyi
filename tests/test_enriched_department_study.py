import json
from evaluation.core_exploration.enriched_department_study import build_docs


def fixture(tmp_path):
    p=tmp_path/'doctors.json'
    p.write_text(json.dumps({'doctors':[{'department':'骨科','specialty':'骨折与关节问题','name':'不得入文档',
                                       'education':'不得入文档','specialties':['骨折','骨折']},
                                      {'department':'普外科','specialty':'腹部手术'}]},ensure_ascii=False),encoding='utf-8')
    return p


def test_enrichment_uses_only_matching_specialty_fields(tmp_path):
    docs,meta,hashes=build_docs(['骨科','普外科'],[fixture(tmp_path)])
    assert '骨折与关节问题' in docs[0] and '腹部手术' in docs[1]
    assert all('不得入文档' not in d for d in docs)
    assert meta[0]['distinct_resource_texts']==2
    assert hashes


def test_adult_parent_description_is_not_added_to_child_specialty(tmp_path):
    docs,meta,_=build_docs(['小儿骨科'],[fixture(tmp_path)])
    assert docs==['小儿骨科']
    assert meta[0]['distinct_resource_texts']==0


def test_document_length_and_truncation_are_recorded(tmp_path):
    p=tmp_path/'long.json';p.write_text(json.dumps({'doctors':[{'department':'骨科','specialty':'骨'*1000}]}),encoding='utf-8')
    docs,meta,_=build_docs(['骨科'],[p])
    assert len(docs[0])==800 and meta[0]['character_truncated']
