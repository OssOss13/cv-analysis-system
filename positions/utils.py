import hashlib

def compute_file_hash(django_file):
    file_bytes = django_file.read()     
    django_file.seek(0)                 
    return hashlib.sha256(file_bytes).hexdigest()
