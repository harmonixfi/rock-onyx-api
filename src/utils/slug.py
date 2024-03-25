import re

def slugify(text):
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', text).strip().lower()
    slug = re.sub(r'\s+', '-', slug)
    return slug