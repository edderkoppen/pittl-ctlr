F1="pigpiod.service"
F2="pittld.service"
SYSTEMDIR="/lib/systemd/system"

HERE=$(dirname $(readlink -f "$0"))
SRCDIR="$HERE/../src"

echo "Installing pigpio"
rm pigpio.zip
sudo rm -rf PIGPIO
wget abyz.me.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd PIGPIO
make
sudo make install

echo "Installing python libraries"
cd "$SRCDIR"
python3 "$SRCDIR/setup.py" install

echo "Adding systemd units"
cp "$HERE/pigpiod.service" "$SYSTEMDIR"
cp "$HERE/pittl-ctlr.service" "$SYSTEMDIR"

systemctl daemon-reload
systemctl enable pigpiod.service
systemctl enable pittl-ctlr.service

echo "Done"
echo "Reboot system for changes to take effect"
