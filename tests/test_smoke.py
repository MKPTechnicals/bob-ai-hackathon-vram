from src.data import generate_synthetic_data
from src.model import ForecastModel, AnomalyDetector
from src.optimizer import recommend_actions
from src.bob_integration import generate_operator_brief


def test_pipeline_smoke():
    df = generate_synthetic_data(days=2)
    assert not df.empty

    fm = ForecastModel()
    fm.train(df)
    preds = fm.predict_hours(6)
    assert len(preds) == 6

    ad = AnomalyDetector()
    ad.train(df)
    an = ad.detect_recent(df, window_hours=24)
    assert 'count' in an

    actions = recommend_actions(preds, an)
    assert isinstance(actions, dict)

    brief = generate_operator_brief(preds, an, actions)
    assert 'brief' in brief
