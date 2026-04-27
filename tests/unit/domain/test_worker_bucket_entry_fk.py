from docuflow.domain.entities.production import WorkerBucketEntry


def test_worker_bucket_entry_has_task_group_id():
    entry = WorkerBucketEntry(node_id="LASER_1", task_item_id=1)
    assert hasattr(entry, "task_group_id")
    assert entry.task_group_id is None
