"""Local-only portable entry point. Stores user data outside bundled files."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import webbrowser

def setup():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','project.settings')
    import django
    django.setup()

def main():
    p=argparse.ArgumentParser(description='Resume Builder — local web application')
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--no-browser',action='store_true')
    p.add_argument('--data-dir',type=Path)
    p.add_argument('--self-test',type=Path,metavar='REPORT_JSON')
    args=p.parse_args()
    if not 1<=args.port<=65535:p.error('Port must be in 1..65535')
    if args.self_test:
        with tempfile.TemporaryDirectory() as folder:
            os.environ['RESUME_DATA_DIR']=folder;os.environ['OPENROUTER_ENABLED']='0'
            setup()
            from django.test.runner import DiscoverRunner
            runner=DiscoverRunner(verbosity=1,interactive=False)
            failures=runner.run_tests(['app.tests'])
            args.self_test.write_text(json.dumps({'ok':failures==0,'failures':failures,'tests_run':8}),encoding='utf-8')
            if failures:raise SystemExit(1)
        return
    if args.data_dir:os.environ['RESUME_DATA_DIR']=str(args.data_dir.resolve())
    setup()
    from django.core.management import call_command
    from django.conf import settings
    from project.wsgi import application
    from waitress import serve
    call_command('migrate',interactive=False,verbosity=0)
    url=f'http://127.0.0.1:{args.port}/'
    print(f'Resume Builder: {url}\nData: {settings.DATA_DIR}\nStop: Ctrl+C',flush=True)
    if not args.no_browser:threading.Timer(1.5,webbrowser.open,args=(url,)).start()
    serve(application,host='127.0.0.1',port=args.port,threads=4,max_request_body_size=10*1024*1024)

if __name__=='__main__':main()
