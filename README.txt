COMPRESSOR OPTIMIZER - LOCAL OFFLINE TOOL

How to run:
1. Open terminal in this project folder
2. Create venv
3. Activate venv
4. Install requirements
5. Run main.py

CMD commands:

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

EXE build command:

pyinstaller --noconfirm --clean --onefile --windowed --name "Compressor_Optimizer" main.py

EXE output:
dist\Compressor_Optimizer.exe
