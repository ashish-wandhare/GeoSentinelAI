# GeoSentinel AI

GeoAI-Powered Urban Waterlogging Intelligence & Early Warning Platform

## Objective

Develop a geospatial machine learning platform that estimates urban
waterlogging risk, identifies geographic hotspots, monitors changing
conditions, and supports location-aware early warnings.

## Initial Scope

- Geography: Hyderabad, Telangana, India
- Data: Historical/open real data plus synthetic test data
- Frontend: Streamlit dashboard and interactive map
- Backend: FastAPI
- Database: PostgreSQL with PostGIS
- Machine learning: scikit-learn
- Experiment tracking: MLflow
- Monitoring: Prometheus and Grafana
- Initial deployment: Local development, followed by Docker Compose

## Development Principles

- Separate observed incidents from predicted risk.
- Track data provenance and freshness.
- Keep synthetic data separate from real-world evaluation data.
- Evaluate models using leakage-aware validation.
- Minimize infrastructure cost and resource consumption.
- Protect user location and application credentials.

## Current Status

Phase 1: Project foundation created.

Phase 2: Configuration and dependency setup in progress.

No real-world prediction capability is claimed until the data pipeline,
model evaluation, and application integration have been implemented
and tested.

## Getting Started

Activate the Python virtual environment and install dependencies
using the instructions in the project documentation.

## License

To be determined after reviewing the licenses of included datasets
and dependencies.
