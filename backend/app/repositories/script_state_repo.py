from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import ScriptState


def get_state(db: Session, script_name: str) -> str | None:
    state = db.query(ScriptState).filter(ScriptState.script_name == script_name).first()
    return state.last_position if state else None


def set_state(db: Session, script_name: str, last_position: str) -> ScriptState:
    state = db.query(ScriptState).filter(ScriptState.script_name == script_name).first()
    if state:
        state.last_position = last_position
        state.updated_at = datetime.now(timezone.utc)
    else:
        state = ScriptState(script_name=script_name, last_position=last_position)
        db.add(state)
    db.commit()
    db.refresh(state)
    return state