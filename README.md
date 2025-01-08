# videoAnnotation_backend

This repo is only for local server running on the same machine with the client.

## Quick Start

We are using a Python server and MongoDB in the backend.

### Prerequisites

Before we begin, make sure you have [Docker]((https://www.docker.com/)) installed. Docker is required to pull and run MongoDB image. If you haven't installed it, please follow the instruction on the official site to download and install Docker for your operating system. You don't really need a docker account for now.

You can either use the Docker Desktop GUI or CLI for the following operations. Here we use CLI. 
Run the command to test the installation:
```
docker -v
```

### Step 1: Pull MongoDB image from DockerHub and run the container  

You may want to check out the official DockerHub [page](https://hub.docker.com/_/mongo) of the image.

Pull the image:
```
docker pull mongo
```

Then run the container:
```
docker run -d \
    --name mongodb \
    -p 27017:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=admin \
    -e MONGO_INITDB_ROOT_PASSWORD=secret \
    -v /yourdirectory/db:/data/db \
    mongo
```
* -d: Run the container in detached mode.
* --name mongodb: Assign a name to the container.
* -p 27017:27017: Map port 27017 of the host to port 27017 of the container.
* -e MONGO_INITDB_ROOT_USERNAME=admin: Set the MongoDB root username.
* -e MONGO_INITDB_ROOT_PASSWORD=secret: Set the MongoDB root password.
* -v /yourlocaldirectory/db:/data/db: Mount a local volume to persist data.


You can stop the container and start it again using these commands:
```
docker stop mongodb
docker start mongodb
```

### Step 2: Clone this repo

### Step 3: create the database.int file

We need to create the database.int file, so that the server can read the information from the file to connect to the database. Remember to add it to .gitignore if you don't want others to see your credential.

Create a new file in the root directory. Name it as database.int. Add these contents to the file:
```
[mongodb]
host=localhost
port=27017
dbname=mongodb
user=admin
password=secret
```

### Step 4: Install dependencies

It's highly recommended to use a virtual environment manangement tool. Here we use a python built-in package called venv.

> [!NOTE]
> We have seen issues with Python 3.12+. For your information, the Python version we are using is 3.10.

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

### Step 5: Run the development server

```bash
cd src
uvicorn main:app --reload
```

Now the server is running on http://127.0.0.1:8000 and listening to the requests from the [client](https://github.com/JaneliaSciComp/videoAnnotation).

To test whether the server is running, go to http://localhost:8000/test. You should see a message "I am ready!".

### (Optional) Step 6: Add customized data processing function to customized.py 

This file is for the developer to add their own function to process the additional data associated with each video if they have turned on the `additionalFields` attribute of `<VideoManager>` in the client. Please refer to the file for details.