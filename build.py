import os
from pathlib import Path
import sys
import PyInstaller.__main__

ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
NAME='ResumeBuilder'
args=['--noconfirm','--onedir','--console','--name',NAME,'--distpath','dist','--workpath','build','--specpath','build']
for name in ['IPython','tensorboard','mlxtend','pythoncom','pywintypes','win32com','PySide6','PyQt5','tensorflow','jax','pytest']+['torch', 'torchvision', 'cv2', 'streamlit', 'datasets', 'pyarrow', 'pandas', 'numpy', 'matplotlib', 'scipy']:
    args+=['--exclude-module',name]
for name in ['Django', 'reportlab', 'waitress']:
    args+=['--copy-metadata',name]
for name in ['django']:
    args+=['--collect-all',name]
for src,dst in [('app/templates', 'app/templates'), ('app/static', 'app/static'), ('app/migrations', 'app/migrations')]:
    args+=['--add-data',str(ROOT/src)+os.pathsep+dst]
for name in ['project.settings', 'project.urls', 'project.wsgi', 'app.apps', 'app.models', 'app.forms', 'app.views', 'app.tests', 'app.migrations', 'app.migrations.0001_initial', 'app.migrations.0002_evententry_created_at_alter_evententry_name_and_more', 'django.db.backends.sqlite3']:
    args+=['--hidden-import',name]
args.append('run.py')
PyInstaller.__main__.run(args)

# Some Python distributions carry additional TLS certificate policy data.
import shutil
policy=Path(sys.base_prefix)/"Lib"/"codex-rejected-cas.pem"
if policy.is_file():shutil.copy2(policy,ROOT/"dist"/NAME/"_internal"/policy.name)
