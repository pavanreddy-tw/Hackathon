sudo apt update
sudo apt install -y python3-pip

sudo pip3 install virtualenv
virtualenv venv
source venv/bin/activate

pip install -r requirements.txt

streamlit run server.py --server.port 8501 --server.address 0.0.0.0
