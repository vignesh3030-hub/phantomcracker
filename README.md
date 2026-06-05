 that combines hashcat + John + CME + Hydra into one script with real-time alerts and automatic validation.

 
 # 1. Run it (auto-detects rockyou, auto-detects hash type)
python3 phantomcracker.py test.txt

# 2. Or specify the hash type
python3 phantomcracker.py test.txt -m 1000

# 3. Or crack + validate against a live target
python3 phantomcracker.py test.txt -m 1000 -t 192.168.1.100

# 4. Quick crack only
python3 phantomcracker.py test.txt -m 1000 --no-validate
