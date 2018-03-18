import os

def url(path):
    base_path = os.getenv("AN_URL")
    if base_path is None:
        base_path = "http://localhost/annotatron/"
    return base_path + path