mkdir build
cd build
cmake ..
make -j12
make install
cd ..
sudo ln -s /usr/local/lib/libmynteye_depth.so /usr/lib/libmynteye_depth.so.1
