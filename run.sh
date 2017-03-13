echo "#INSTALLING DEPENDENCIES"
echo "========================"
cat requirements.txt 
pip install -r requirements.txt > /dev/null
echo "#Starting MongoDB"
echo "================="
docker run -d -p 27017:27017 mongo:latest >/dev/null
echo "#Starting Redis"
echo "==============="
docker run -d -p 6379:6379 redis:alpine >/dev/null
echo "#Starting Reverse Proxy"
echo "======================="
python reverseProxy.py
 
