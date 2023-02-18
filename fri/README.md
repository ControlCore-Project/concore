# The Control-Core FRI for Closed-Loop Neuromodulation Control Systems

The Control-Core File Receiving Interface (FRI) is built with is Python-3.10. It is the core component that makes the distributed executions a reality in the Control-Core framework.

# Install Dependencies

Install Jupyter lab
````
$ pip install jupyterlab
````

# Running the FRI and a quick test.

To run the FRI as a server:
````
$ cd conore/fri

$ git checkout dev

$ cd server

$ python3 main.py
````

To test:
````
$ cd ..

$ python3 test.py
````

