# Workflows TODO app

This an example project for using workflows to produce a very basic todo application.
The aim of this project is to explain how workflows works to that end they will hopefully be lots of comments.

## TODO

    [] add submodule for workflows engine

## Install

```bash
git clone git@github.com:nocturnalastro/workflows_todo.git

cd workflows_todo_app
pip install -r pip-requirements.txt

cd engine
pip install -r pip-requirements.txt
pip install .

# cd client
# npm install
```

## Running

To run the react client (from `workflows_todo_app/client`)

```bash
export REACT_APP_WF_SERVER=http://localhost:5000
export REACT_APP_WF_GETPATH=/todo/
export PUBLIC_URL=/todo/
npm start
```

To run server (from `workflows_todo_app`)

```bash
export FLASK_APP=app.py
flask run
```

Then visit [http://localhost:8059/todo](http://localhost:8059/todo)
