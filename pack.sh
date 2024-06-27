mkdir -p build/python/lib/python3.12/site-packages 
cp -R phhelper build/python/lib/python3.12/site-packages
cd build
zip -q -r ../phhelper.zip python
cd ..