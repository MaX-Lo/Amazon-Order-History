
def save_file(file_path: str, data: str):
    with open(file_path, 'w') as fh:
        fh.write(data)
