def get_resource_usage(
    resource_id,
    resource_type,
    scheduled_interviews
):
    """
    Count how many scheduled interviews are using
    a particular room or panel.
    """

    count = 0

    for interview in scheduled_interviews:

        if resource_type == "room":
            if interview["room_id"] == resource_id:
                count += 1

        elif resource_type == "panel":
            if interview["panel_id"] == resource_id:
                count += 1

    return count