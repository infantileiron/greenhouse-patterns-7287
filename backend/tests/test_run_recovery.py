"""验证运行中断恢复、重复领取去重与晚到结果栅栏。"""
import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.config.database import get, save, now, transition_run
from src.services.run import (
    create_run, claim_run, finish_run, execute_run, recover_stale_runs,
)
from src.services.review import create_review

PARAMS = {'min_support': .1, 'min_confidence': .5, 'permutations': 99, 'seed': 261105}


def make_study():
    rows = []
    for i in range(24):
        symptoms = ['叶斑'] if i % 2 else ['叶斑', '黄化']
        if i % 3 == 0:
            symptoms.append('萎蔫')
        rows.append({'plant_id': f'P{i:03}', 'greenhouse': f'G{1 + i % 2}', 'symptoms': symptoms})
    dataset = save('datasets', {'name': '测试样本', 'filename': 't.csv', 'rows': rows, 'checksum': 'x'})
    return save('studies', {'name': '测试研究', 'dataset_id': dataset['id'], **PARAMS})


def new_run(study):
    return create_run(SimpleNamespace(study_id=study['id']))


def backdate(record_id, token, seconds=3600):
    """把认领时间改到过去，模拟执行者失联、租约过期。"""
    old = (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()
    assert transition_run(record_id, {'claimed_at': old},
                          expect_statuses=('running',), expect_token=token)


def test_interrupted_run_recovers_and_completes():
    study = make_study()
    stuck = new_run(study)
    claimed = claim_run(stuck['id'])
    assert claimed and claimed[0]['status'] == 'running'
    backdate(stuck['id'], claimed[1])

    # 卡死的运行占着活跃名额：再建2个后第4个被拒绝
    new_run(study)
    new_run(study)
    with pytest.raises(HTTPException) as exc:
        new_run(study)
    assert exc.value.status_code == 429

    recovered = recover_stale_runs()
    assert recovered == [stuck['id']]
    row = get('runs', stuck['id'])
    assert row['status'] == 'recovering'
    assert '中断' in row['error']  # 中断原因保留，页面据此展示恢复重试
    with pytest.raises(HTTPException):  # 恢复重试中仍占名额
        new_run(study)

    done = execute_run(stuck['id'])  # 新执行者接手
    assert done['status'] == 'succeeded'
    assert done['attempts'] == 2
    assert done['error'] is None
    assert done['result']['sample_count'] == 24
    assert get('runs', stuck['id'])['result'] == done['result']

    new_run(study)  # 名额已释放


def test_duplicate_claim_has_single_winner():
    study = make_study()
    run = new_run(study)

    first = claim_run(run['id'])
    assert first is not None
    assert claim_run(run['id']) is None  # 已运行，不能再领
    assert execute_run(run['id']) is None  # 已被认领：重复送达无效

    other = new_run(study)
    winners = []

    def race():
        got = claim_run(other['id'])
        if got:
            winners.append(got[1])

    threads = [threading.Thread(target=race) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(winners) == 1  # 多名执行者同时接手，只有一个有效

    backdate(other['id'], winners[0])  # 获胜者失联，由新执行者接管完成
    recover_stale_runs()
    finished = execute_run(other['id'])
    assert finished['status'] == 'succeeded'
    again = execute_run(other['id'])  # 已终结：重复送达不再计算
    assert again is None
    assert get('runs', other['id'])['result'] == finished['result']


def test_late_result_cannot_overwrite_evidence():
    study = make_study()
    run = new_run(study)
    _, token_a = claim_run(run['id'])  # 执行者A认领后失联
    backdate(run['id'], token_a)

    recover_stale_runs()
    done_b = execute_run(run['id'])  # 执行者B接管并完成
    assert done_b['status'] == 'succeeded'

    late = finish_run(run['id'], token_a, {  # A醒来的晚到结果
        'status': 'succeeded', 'result': {'rules': [], 'forged': True},
        'error': None, 'finished_at': now(),
    })
    assert late is None
    row = get('runs', run['id'])
    assert row['status'] == 'succeeded'
    assert row['result'] == done_b['result']  # 证据未被改写
    assert row['result'].get('sample_count') == 24
    assert row['attempts'] == 2

    review = create_review(  # 复查只引用这份成功结果
        SimpleNamespace(run_id=run['id'], rule_ids=[r['rule_id'] for r in row['result']['rules'][:1]], note='复查'),
        {'email': 'analyst@nanling.test'})
    assert review['status'] == 'pending'


def test_review_rejects_non_succeeded_run():
    study = make_study()
    run = new_run(study)
    with pytest.raises(HTTPException) as exc:
        create_review(SimpleNamespace(run_id=run['id'], rule_ids=[], note='复查'), {'email': 'a@b.c'})
    assert exc.value.status_code == 409

    claim = claim_run(run['id'])
    backdate(run['id'], claim[1])
    recover_stale_runs()
    with pytest.raises(HTTPException) as exc:  # 恢复重试中同样不能提交复查
        create_review(SimpleNamespace(run_id=run['id'], rule_ids=[], note='复查'), {'email': 'a@b.c'})
    assert exc.value.status_code == 409


def test_repeated_interruption_eventually_fails_with_reason(monkeypatch):
    monkeypatch.setattr('src.services.run.MAX_ATTEMPTS', 2)
    study = make_study()
    run = new_run(study)

    claim = claim_run(run['id'])
    backdate(run['id'], claim[1])
    recover_stale_runs()
    assert get('runs', run['id'])['status'] == 'recovering'

    claim = claim_run(run['id'])  # 第2次尝试再次中断
    assert claim[0]['attempts'] == 2
    backdate(run['id'], claim[1])
    recover_stale_runs()
    row = get('runs', run['id'])
    assert row['status'] == 'failed'
    assert '中断' in row['error']  # 失败原因保留
