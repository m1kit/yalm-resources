import shutil


def generate(dest, meta):
  print(f"Copying static files...")
  shutil.copytree('static/dist', dest, dirs_exist_ok=True)
