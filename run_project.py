"""Rebuild the entire project from bundled public sources. Python 3.12 recommended."""
from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('OMP_NUM_THREADS','4');os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
steps=['download_data.py','warehouse.py','modeling.py','policy.py','business.py','tableau_workbook.py','report.py','make_notebook.py']
for step in steps:
    print('\nRUN',step,flush=True)
    subprocess.run([sys.executable,str(ROOT/'src'/step)],cwd=ROOT,check=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
print('Complete. Open reports/MetroPredict_Project_Report.pdf or tableau/MetroPredict.twbx.')
