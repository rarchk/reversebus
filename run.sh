echo "#INSTALLING DEPENDENCIES"
echo "========================"
cat requirements.txt 
pip install -r requirements.txt > /dev/null
echo
echo "#Starting MongoDB"
echo "================="
docker run -d -p 27017:27017 mongo:latest  >/dev/null
echo
echo "#Starting Redis"
echo "==============="
docker run -d -p 6379:6379 redis:alpine >/dev/null
echo
echo "#Starting Reverse Proxy"
echo "======================="
python src/reverseProxy.py
 
