pip install -r requirements.txt
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 27017:27017 mongo:latest
python reverseProxy.py
 
