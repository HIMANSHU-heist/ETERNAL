_last_chart: dict[str, dict] = {}

def set_last_chart(file_id: str, chart_ctx: dict) -> None:
    _last_chart[file_id] = chart_ctx

def get_last_chart(file_id: str) -> dict | None:
    return _last_chart.get(file_id)