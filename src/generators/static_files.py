import shutil


def generate(dest, meta):
  print(f"Copying static files...")
  shutil.copytree('static/raw', dest, dirs_exist_ok=True)
