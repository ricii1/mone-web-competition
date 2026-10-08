from uuid import UUID


def class_channel(class_id: UUID) -> str:
    return f"class:{class_id}:events"


def material_channel(material_id: UUID) -> str:
    return f"material:{material_id}:progress"


def live_session_channel(session_id: UUID) -> str:
    return f"live:{session_id}"
