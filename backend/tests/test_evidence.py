import base64
import hashlib
import json
from pathlib import Path

import pytest

from backend.artifacts.evidence import EVIDENCE_HEADER, embed_evidence_figures, parse_evidence_bundle
from backend.context.extraction import extract_upload
from backend.core.runs import create_run, make_run_executor
from backend.pipelines.essay_html import build_essay_html_prompt

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jB0cAAAAASUVORK5CYII=')


def bundle(data=PNG, **overrides):
    row = {'id':'task1-local','caption':'Task 1 <original> screenshot','media_type':'image/png',
           'data_base64':base64.b64encode(data).decode(), 'sha256':hashlib.sha256(data).hexdigest()}
    row.update(overrides)
    return EVIDENCE_HEADER + json.dumps({'figures':[row]})


@pytest.mark.parametrize('override', [
    {'media_type':'image/svg+xml'}, {'sha256':'wrong'}, {'id':'../outside'},
    {'data_base64':'<script>invalid</script>'}, {'data_base64':base64.b64encode(b'not an image').decode()},
])
def test_unsafe_or_corrupt_evidence_is_rejected(override):
    with pytest.raises(ValueError):
        parse_evidence_bundle(bundle(**override))


def test_original_images_are_embedded_and_captions_escaped():
    figures=parse_evidence_bundle(bundle())
    output=embed_evidence_figures('<html><body><p>[[EVIDENCE:task1-local]]</p></body></html>',figures)
    assert 'data:image/png;base64,'+base64.b64encode(PNG).decode() in output
    assert '<p><figure' not in output
    assert '&lt;original&gt;' in output
    assert '[[EVIDENCE:' not in output
    fallback=embed_evidence_figures('<html><body>Text</body></html>',figures)
    assert fallback.index('evidence-appendix') < fallback.index('</body>')


def test_large_screenshot_bypasses_text_truncation_but_not_model_budget(tmp_path):
    # Trailing bytes preserve the tiny PNG while exercising the previous 50k cap.
    text=bundle(PNG+b'\0'*60000)
    path=tmp_path/'evidence.txt'
    path.write_text(text)
    extraction=extract_upload({'id':'upl_1','original_name':'evidence.txt','media_type':'text/plain',
                              'stored_path':str(path),'size_bytes':path.stat().st_size})
    assert len(extraction.evidence_figures)==1
    assert len(extraction.as_context_text()) < 1000
    assert 'data_base64' not in extraction.as_context_text()
    assert extraction.to_summary_dict()['evidence_figure_ids']==['task1-local']
    path.write_text(EVIDENCE_HEADER+'invalid-json')
    invalid=extract_upload({'id':'upl_1','original_name':'evidence.txt','stored_path':str(path)})
    assert not invalid.evidence_figures and invalid.notes


def test_owner_scoped_uploaded_evidence_reaches_essay_without_sending_pixels_to_model(
    tmp_path, repo_with_user, fake_model_provider_factory, mock_pdf_converter, noop_search_adapter,
):
    repo,user=repo_with_user
    text=bundle()
    path=tmp_path/'evidence.txt'
    path.write_text(text)
    repo.create_upload(id='upl_evidence',user_id=user['id'],original_name='evidence.txt',media_type='text/plain',
                       stored_path=str(path),sha256=hashlib.sha256(text.encode()).hexdigest(),size_bytes=path.stat().st_size)
    provider=fake_model_provider_factory('<!doctype html><html><body><p>[[EVIDENCE:task1-local]]</p></body></html>')
    result=create_run(repo,current_user=user,request={'task_text':'BA3073 deployment evidence test',
        'intent':'essay_latex','search_mode':'off','upload_ids':['upl_evidence']},
        workspace_root=str(tmp_path/'workspace'),executor=make_run_executor(provider,pdf_converter=mock_pdf_converter),
        search_adapter=noop_search_adapter)
    assert result['status']=='succeeded'
    output=(Path(result['output_root'])/'output/main.html').read_text()
    assert 'data:image/png;base64,' in output
    assert base64.b64encode(PNG).decode() not in provider.requests[0].user_prompt


def test_assignment_prompt_demands_truthful_bounded_report():
    system,_=build_essay_html_prompt(task_text='BA3073 From AI Agent to Cloud Service',context_bundle='',options={},search={})
    assert '20 A4 pages' in system
    assert 'Never fabricate' in system
    assert 'Task 1' in system and 'Task 2' in system and 'Task 3' in system
