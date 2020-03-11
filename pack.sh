cp -R phhelper build/python/lib/python3.7/site-packages
cp -R phhelper build/python/lib/python3.8/site-packages
cd build
zip -q -r ../../phhelper.zip python
cd ..
