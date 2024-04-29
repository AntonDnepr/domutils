def clean_search_string(search_string: str) -> str:
    """
    Cleans a search string by trimming leading and trailing whitespace.

    Args:
        search_string (str): The search string to clean.

    Returns:
        str: The cleaned search string.
    """
    if search_string.endswith(("-", "'", '"', ",")):
        search_string = search_string[:-1]
    return search_string.strip().replace("(", "").replace(")", "").replace("=", "")
