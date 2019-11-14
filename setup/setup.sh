F1="pigpiod.service"
F2="pittl-ctlr.service"
SYSTEMDIR="/lib/systemd/system"

HERE=$(dirname $(readlink -f "$0"))
CODEDIR="$HERE/../code"

echo "Performing python install"
cd "$CODEDIR"
python3 "$CODEDIR/setup.py" install

echo "Adding systemd units"
cp "$HERE/pigpiod.service" "$SYSTEMDIR"
cp "$HERE/pittl-ctlr.service" "$SYSTEMDIR"

systemctl daemon-reload
systemctl enable pigpiod.service
systemctl enable pittl-ctlr.service

echo "Done"
echo "Reboot system for changes to take effect"
