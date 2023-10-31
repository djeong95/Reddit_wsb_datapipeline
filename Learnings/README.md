# Learnings while constructing this data pipeline
These are my notes taken to understand all the in's and out's of constructing data pipelines at a high level. 

## Airflow (running locally without Docker)
- Here is the [Youtube tutorial](https://www.youtube.com/watch?v=z7xyNOF8tak&list=PLwFJcsJ61oujAqYpMp1kdUBcPG0sE0QMT&index=2&ab_channel=coder2j) that guides you on how to install Airflow, create a Conda virtual environment, run commands such as:
```bash
# To create an environment with Anaconda:
Conda create -n airflow python=3.9
Conda activate airflow

# To create an environment with Virtualenv, use this instead:
$ pip install virtualenv
$ python3 -m venv venv
$ source venv/bin/activate

# Install Apache Airflow as shown in the video

# Then, run below commands to run Airflow locally
export AIRFLOW_HOME=~/airflow
airflow db init
airflow users create --username admin --firstname firstname --lastname lastname --role Admin --email admin@admin.com
airflow webserver -p 8080
airflow scheduler
```
- Here is a link to [Apache Airflow documentations](https://airflow.apache.org/docs/apache-airflow/stable/start.html) on how to get started as well.
    

## HyperText Transfer Protocol (HTTP) 

HTTP has been the foundation for data communication for the World Wide Web (i.e. internet) since 1990. HTTP is a generic and stateless protocol which can be used for other purposes as well using extensions of its request methods, error codes, and headers.

Basically, HTTP is a TCP/IP based communication protocol, that is used to deliver data (HTML files, image files, query results, etc.) on the World Wide Web. The default port is TCP 80, but other ports can be used as well. It provides a standardized way for computers to communicate with each other. HTTP specification specifies how clients' request data will be constructed and sent to the server, and how the servers respond to these requests.

### Basic Features
There are three basic features that make HTTP a simple but powerful protocol:

- **HTTP is connectionless:** The HTTP client, i.e., a browser initiates an HTTP request and after a request is made, the client waits for the response. The server processes the request and sends a response back after which client disconnect the connection. So client and server knows about each other during current request and response only. Further requests are made on new connection like client and server are new to each other.

- **HTTP is media independent:** It means, any type of data can be sent by HTTP as long as both the client and the server know how to handle the data content. It is required for the client as well as the server to specify the content type using appropriate MIME-type.

- **HTTP is stateless:** As mentioned above, HTTP is connectionless and it is a direct result of HTTP being a stateless protocol. The server and client are aware of each other only during a current request. Afterwards, both of them forget about each other. Due to this nature of the protocol, neither the client nor the browser can retain information between different requests across the web pages.

### What is stateless?

A stateless architecture or application is a type of Internet protocol where the state of the previous transactions is neither stored nor referenced in subsequent transactions. Each request sent between the sender and receiver can be interpreted and does not need earlier requests for its execution. This is a protocol where a client and server request and response are made in a current state. In addition, the status of the current session is not retained or carried over to the next transaction. 


### What is stateful?

Stateful architecture or application describes a structure that allows users to store, record, and return to already established information and processes over the internet. It entails transactions that are performed using past transactions as a reference point. In stateful applications, the current transaction can be affected by the previous ones. 



### What is TCP/IP based communication protocol?


https://www.tutorialspoint.com/http/http_overview.htm

https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview#http_messages




