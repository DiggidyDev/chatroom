def content(**kwargs):
    """
    Correctly format content for outgoing
    :param kwargs:
    :return:
    """
    struct = {
        "content": kwargs["content"],
        "system-message": kwargs["system_message"],
        "user": kwargs["user"]
    }

    return struct
