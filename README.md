Para instalação do projeto via Linux é simples, abra seu terminal e execute os seguintes comandos

1 - Clone o repositório com:

git clone https://github.com/gaby1916/Ouvidoria.git

2 - Entre na pasta do repositorio que acabastes de clonar com:

cd Ouvidoria

3 - Crie um ambiente virtual com python:

python3 -m venv /root/Ouvidoria (ou o caminho exato onde tenha feito a clonagem do repositório)

4 - Ative o ambiente virtual com:

cd bin && source activate && cd ..

5 - Instale os requisitos necessários com:

pip3 install -r requirements.txt

6 - Por fim execute a aplicação com o seguinte comando:

flask run --debug --host=0.0.0.0 --port=5000 (ou se preferir escolha outros parametros disponibilizados pelo flask).

--------------------------------------------------------------------------------------------------------------------------

Instalação via Windows (usando Visual Studio Code)

Abra o VS Code e acesse o terminal integrado (Ctrl + ²).

Clone o repositório:

git clone https://github.com/gaby1916/Ouvidoria.git


Entre na pasta do projeto:

cd Ouvidoria


Crie um ambiente virtual com Python:

python -m venv venv


Ative o ambiente virtual:

venv\Scripts\activate


Instale as dependências:

pip install -r requirements.txt


Execute a aplicação Flask:

flask run --debug


(por padrão, a aplicação rodará em http://127.0.0.1:5000/)
