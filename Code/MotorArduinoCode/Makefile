default:
	rm -rf build/
	arduino-cli compile --fqbn arduino:avr:mega --build-path ./build .
	arduino-cli upload -p /dev/ttyACM2  --input-dir ./build/ --fqbn arduino:avr:mega .
