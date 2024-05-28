def clean_search_string(search_string: str) -> str:
    """
    Cleans a search string by trimming leading and trailing whitespace.

    Args:
        search_string (str): The search string to clean.

    Returns:
        str: The cleaned search string.
    """
    if search_string.endswith(("-", "'", '"', ",", ";")):
        search_string = search_string[:-1]
    return (
        search_string.strip()
        .replace("(", "")
        .replace(")", "")
        .replace("=", "")
        .replace(";", "")
    )


def check_if_int(string: str) -> bool:
    try:
        int(string)
        return True
    except ValueError:
        return False
    return False
