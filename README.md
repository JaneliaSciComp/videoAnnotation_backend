# videoAnnotation_backend


## Quick Start

### Step 1: Clone this repo, and checkout local_usage branch

This repo is only for local server running on the same machine as the client.

### Step 2: Install dependencies

It's highly recommended to use a virtual environment manangement tool. Here we use a python  built-in package called venv.

```bash
cd videoAnnotation_backend
python3 -m venv env  # create env dir
source env/bin/activate  #activate
pip install -r requirements.txt  # install dependencies
```

If everything goes well, you should be able to go to next step to start the server. In case you see a ModuleNotFoundError, try to re-activate the env:
```bash
deactivate
source env/bin/activate  #activate
```

### Step 3: Run the development server

```bash
cd src
uvicorn main:app --reload
```

Now the server is running on http://127.0.0.1:8000. 