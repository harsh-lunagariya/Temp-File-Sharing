from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep


DELETE_RETRY_COUNT = 3
DELETE_RETRY_DELAY_SECONDS = 0.2
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='file-cleanup')


def delete_file(path_value: str | None):
    if not path_value:
        return

    path = Path(path_value)
    for attempt in range(DELETE_RETRY_COUNT):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == DELETE_RETRY_COUNT - 1:
                return
            sleep(DELETE_RETRY_DELAY_SECONDS)


def delete_file_async(path_value: str | None):
    _executor.submit(delete_file, path_value)
