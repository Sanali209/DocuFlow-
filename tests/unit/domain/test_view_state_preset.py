from docuflow.domain.entities.production import ViewPreset, ViewState


def test_view_state_fields():
    vs = ViewState(user_id="admin", view_name="task_board", entity_type="project", entity_id="1")
    assert vs.is_expanded is True


def test_view_preset_fields():
    vp = ViewPreset(
        name="My Filter",
        user_id="admin",
        view_name="task_board",
        filters_json="{}",
    )
    assert vp.is_default is False
