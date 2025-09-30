Cache Operator example using [Kuroboros](https://github.com/jedwards94/kuroboros).
Creates a Deployment of a given cache type and check for its status
## Run
run with minikube
```
minikube start
python -m venv .venv
pip install .
kuroboros build
minikube image load cache-operator:v0.0.1
kuroboros deploy test
kubectl apply -f example.yaml
```