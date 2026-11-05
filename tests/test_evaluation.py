import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from evaluation.evaluator import evaluate_cases, predict_tool, threshold
from evaluation.test_cases import TEST_CASES


def test_full_fixture_pass():
    answers = {c['question']: c['expected_tool'] for c in TEST_CASES}
    report = evaluate_cases(answers.__getitem__, TEST_CASES)
    assert report['passed'] and report['total'] == report['correct'] == 50


@pytest.mark.parametrize('correct,expected', [(45, True), (44, False)])
def test_quality_boundary(correct, expected):
    answers = {c['question']: c['expected_tool'] if i < correct else 'wrong'
               for i, c in enumerate(TEST_CASES)}
    assert evaluate_cases(answers.__getitem__, TEST_CASES)['passed'] is expected


def test_api_error_blocks_even_above_threshold():
    answers = {c['question']: c['expected_tool'] for c in TEST_CASES}
    def predict(q):
        if q == TEST_CASES[0]['question']:
            raise TimeoutError('sensitive response must not be recorded')
        return answers[q]
    report = evaluate_cases(predict, TEST_CASES)
    assert report['pass_rate'] == 98 and report['errors'] == 1
    assert not report['passed']
    assert 'sensitive' not in json.dumps(report)


@pytest.mark.parametrize('content', ['null', '[]', '1', '{}', '{"tool":[]}',
    '{"tool":"invented"}', '```json\n{"tool":"get_repository"}\n```',
    '{"tool":"get_repository","extra":true}', ''])
def test_invalid_responses(content):
    groq = Mock()
    groq.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content=content))])
    with pytest.raises((ValueError, TypeError)):
        predict_tool(groq, [{'function': {'name': 'get_repository', 'description': ''}}], 'q')


@pytest.mark.parametrize('value', ['89', 'nan', 'inf', '101'])
def test_threshold_cannot_be_lowered(monkeypatch, value):
    monkeypatch.setenv('EVALUATION_MIN_ACCURACY', value)
    with pytest.raises(ValueError):
        threshold()


def test_empty_cases_fail():
    with pytest.raises(ValueError):
        evaluate_cases(lambda _: 'tool', [])


def test_missing_credentials_removes_stale_report(monkeypatch):
    import asyncio
    from evaluation import evaluator
    # Avoid the shared pytest temp root, which may belong to another Windows
    # security context. Create and clean up only this test's unique directory.
    with TemporaryDirectory(prefix="evaluation-test-", dir=Path(__file__).resolve().parents[1]) as directory:
        path = Path(directory) / 'results.json'
        path.write_text('{"passed":true}', encoding='utf-8')
        monkeypatch.setattr(evaluator, 'PREDICTIONS_FILE', path)
        monkeypatch.delenv('GROQ_API_KEY', raising=False)
        with pytest.raises(RuntimeError, match='GROQ_API_KEY'):
            asyncio.run(evaluator.run_evaluation())
        assert not path.exists()


def test_valid_prediction_and_reproducible_request():
    groq = Mock()
    groq.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content='{"tool":"get_repository"}'))])
    assert predict_tool(groq, [{'function': {'name': 'get_repository', 'description': ''}}], 'q') == 'get_repository'
    kwargs = groq.chat.completions.create.call_args.kwargs
    assert kwargs['temperature'] == 0 and kwargs['seed'] == 42
    assert kwargs['reasoning_effort'] == 'low' and kwargs['max_completion_tokens'] == 4096
    assert kwargs['response_format']['json_schema']['strict'] is True
    assert kwargs['response_format']['json_schema']['schema']['properties']['tool']['enum'] == ['get_repository']


def test_cli_error_exits_nonzero_without_leaking_details(monkeypatch, capsys):
    from evaluation import evaluator
    async def fail():
        raise RuntimeError('private provider details')
    monkeypatch.setattr(evaluator, 'run_evaluation', fail)
    with pytest.raises(SystemExit) as exc:
        evaluator.main()
    assert exc.value.code == 1
    assert 'private' not in capsys.readouterr().out


@pytest.mark.parametrize('passed,code', [(True, 0), (False, 1)])
def test_cli_gate_exit_codes(monkeypatch, passed, code):
    from evaluation import evaluator
    async def result():
        return passed
    monkeypatch.setattr(evaluator, 'run_evaluation', result)
    with pytest.raises(SystemExit) as exc:
        evaluator.main()
    assert exc.value.code == code
