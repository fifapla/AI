# mlflowlite — a compact MLOps lifecycle

![CI](https://github.com/<your-user>/mlflowlite/actions/workflows/ci.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green)

The whole model lifecycle in a small codebase you can read in an afternoon: validate data → train → track the run → register a version → pass a promotion gate → serve production → watch for drift.

> 🇪🇬 دورة MLOps مبسّطة: فحص بيانات، تتبع تجارب، سجل نماذج مع بوابة ترقية وتراجع، خدمة نموذج، ومراقبة انحراف البيانات.

## Features
- Data validation: schema, null rates, infinities, class balance, duplicates
- Experiment tracking with a data fingerprint so a metric can be tied to exact data
- Registry with versions and stages, a promotion gate (must beat production, tolerance on other metrics) and one-command rollback
- Model server that always serves the production version and hot-reloads after promote/rollback
- Drift monitor: PSI + KS test per feature with a retrain recommendation
- Reproducible training (fixed seeds) and offline dataset (scikit-learn breast cancer)

## How it works
```
data ─► validate ─► train ─► track run ─► register vN ─► promotion gate ─► production ─► serve /predict
                                                                       ▲                      │
                                                         rollback ◄────┘      drift monitor ◄──┘
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
export PYTHONPATH=src
python -m mlflowlite train --model logreg
python -m mlflowlite promote 1
python -m mlflowlite train --model gboost && python -m mlflowlite promote 2 --min-gain 0.005   # may be BLOCKED: the gate only lets a better model through
python -m mlflowlite drift --shift 2
python -m mlflowlite serve --port 8000
```

## Tests
```bash
python -m unittest discover -s tests -v     # or: pytest
```

## Honest limitations
- Uses a small public dataset; the point is the lifecycle, not the model.
- File-based tracking/registry — swap for MLflow or a database when you need multi-user concurrency.
- Drift is checked on features only; label-delayed performance monitoring is not included.

## Roadmap
- [ ] Prometheus metrics
- [ ] Scheduled drift job + auto-retrain
- [ ] Model signature and input schema enforcement at serving time

## License
MIT
