import sys


def resource_string(file_name: str) -> str:
    """
    Get the value of a file in `collada/resources/{file_name}`
    as a string.

    Parameters
    -----------
    file_name
      The name of the file in `collada/resources/{file_name}`

    Returns
    ----------
    value
      The contents of the file.
    """
    if sys.version_info <= (3, 9):
        from importlib.resources import read_text

        return read_text("collada.resources", file_name)
    else:
        from importlib import resources

        return resources.files("collada").joinpath("resources", file_name).read_text()
